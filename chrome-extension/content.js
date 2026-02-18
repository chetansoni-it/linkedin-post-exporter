chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "START_SCAN") {
        startScan(msg.limit || 100);
    }

    if (msg.type === "EXPORT_VISIBLE") {
        extractJobs(999999); // export whatever is visible
    }
});

async function startScan(limit) {
    await autoScroll(limit);
    extractJobs(limit);
}

/* ================= AUTO SCROLL ================= */

async function autoScroll(limit) {
    let last = 0;
    let stuck = 0;

    while (true) {
        window.scrollBy(0, window.innerHeight);
        await sleep(1500 + Math.random() * 1000);

        const count = document.querySelectorAll("div.feed-shared-update-v2").length;
        if (count >= limit) break;

        if (count === last) {
            stuck++;
            if (stuck >= 3) break;
        } else {
            stuck = 0;
        }
        last = count;
    }
}

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

/* ================= EXTRACTION ================= */

function extractJobs(MAX_POSTS) {
    const seen = new Set();
    const results = [];

    const posts = document.querySelectorAll("div.feed-shared-update-v2");

    posts.forEach(post => {
        if (results.length >= MAX_POSTS) return;

        /* ========= AUTHOR (FINAL, FIXED) ========= */
        let author = "Unknown";

        const headerRoot = post.closest("li") || post;
        const authorSpans = headerRoot.querySelectorAll("span[aria-hidden='true']");

        for (const span of authorSpans) {
            const text = span.innerText
                .replace(/\s+/g, " ")
                .trim();

            if (
                text.length >= 3 &&
                text.length <= 50 &&
                !text.includes("•") &&
                !/^\d/.test(text) &&                 // not starting with number
                !/\b(h|hr|hrs|hour|hours|day|days|w)\b/i.test(text) &&
                !text.includes("Edited") &&
                !text.includes("Visible")
            ) {
                author = text;
                break; // 🔥 THIS WAS MISSING
            }
        }

        /* ========= TIMESTAMP ========= */
        let timestamp = "Unknown";
        post.querySelectorAll("span[aria-hidden='true']").forEach(span => {
            const m = span.innerText.trim().match(/^(\d+\s?[hdw])/i);
            if (m) timestamp = m[1].replace(" ", "");
        });

        /* ========= CONTENT ========= */
        let content = "";
        let longest = "";

        post.querySelectorAll("span[dir='ltr']").forEach(span => {
            const t = span.innerText.replace(/\s+/g, " ").trim();
            if (t.length > longest.length && t.length > 80) {
                longest = t;
            }
        });

        content = longest;
        if (!content) return;

        /* ========= EMAILS ========= */
        let emails = "";
        const emailMatches = content.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi);
        if (emailMatches) {
            emails = [...new Set(emailMatches.map(e => e.toLowerCase()))].join(", ");
        }

        /* ========= CONTACT NUMBERS ========= */
        let contact_numbers = "";

        const phoneMatches = content.match(/(\+?\d[\d\s\-()]{7,}\d)/g);
        if (phoneMatches) {
            const cleaned = phoneMatches
                .map(p => p.replace(/\s+/g, " ").trim())
                .filter(p => p.length >= 8);

            contact_numbers = [...new Set(cleaned)].join(", ");
        }

        /* ========= APPLY LINKS ========= */
        let apply_links = "";
        const links = content.match(/https?:\/\/[^\s)]+/gi);
        if (links) {
            apply_links = [...new Set(links)].join(", ");
        }

        /* ========= JOB FILTER ========= */
        const isJob =
            /hiring|job|apply|vacancy/i.test(content) ||
            emails.length > 0 ||
            apply_links.length > 0;

        if (!isJob) return;

        /* ========= DEDUP ========= */
        const key = author + timestamp + content.slice(0, 120);
        if (seen.has(key)) return;
        seen.add(key);

        results.push({
            author,
            timestamp,
            emails,
            contact_numbers,
            apply_links,
            content
        });
    });

    if (!results.length) {
        alert("No job posts found.");
        return;
    }

    sendCSV(results);
    sendToAPI(results);
}

/* ================= CSV ================= */

function sendCSV(data) {
    const headers = Object.keys(data[0]).join(",");
    const rows = data.map(row =>
        Object.values(row)
            .map(v => `"${String(v).replace(/"/g, '""')}"`)
            .join(",")
    );

    const csv = [headers, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    chrome.runtime.sendMessage({
        type: "DOWNLOAD_CSV",
        url
    });
}

/* ================= API BATCH SENDER ================= */

async function sendToAPI(data) {
    if (!CONFIG.ENABLE_API_SEND) {
        console.log("[LinkedIn Exporter] API sending is disabled in config.");
        return;
    }

    const url = `${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINT}`;
    const batchSize = CONFIG.BATCH_SIZE;
    const totalBatches = Math.ceil(data.length / batchSize);

    console.log(
        `[LinkedIn Exporter] Sending ${data.length} posts to API in ${totalBatches} batch(es) of ${batchSize}...`
    );

    for (let i = 0; i < totalBatches; i++) {
        const batch = data.slice(i * batchSize, (i + 1) * batchSize);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT_MS);

            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ batch_number: i + 1, total_batches: totalBatches, posts: batch }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                console.log(`[LinkedIn Exporter] Batch ${i + 1}/${totalBatches} sent successfully.`);
            } else {
                console.warn(
                    `[LinkedIn Exporter] Batch ${i + 1}/${totalBatches} failed — HTTP ${response.status}`
                );
            }
        } catch (err) {
            if (err.name === "AbortError") {
                console.warn(`[LinkedIn Exporter] Batch ${i + 1}/${totalBatches} timed out.`);
            } else {
                console.error(`[LinkedIn Exporter] Batch ${i + 1}/${totalBatches} error:`, err);
            }
        }

        // Delay between batches to avoid overwhelming the server
        if (i < totalBatches - 1) {
            await sleep(CONFIG.BATCH_DELAY_MS);
        }
    }

    console.log("[LinkedIn Exporter] All batches sent.");
}
