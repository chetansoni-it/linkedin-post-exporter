(function () {
    const MAX_POSTS = 100;
    const seen = new Set();
    const results = [];

    const posts = document.querySelectorAll("div.feed-shared-update-v2");

    posts.forEach(post => {
        if (results.length >= MAX_POSTS) return;

        /* ================= AUTHOR ================= */
        let author = "Unknown";

        const headerRoot =
            post.closest("li") ||
            post.parentElement ||
            post;

        const authorAriaSpans = headerRoot.querySelectorAll("span[aria-hidden='true']");

        for (const span of authorAriaSpans) {
            const text = span.innerText.replace(/\s+/g, " ").trim();

            if (
                text.length >= 3 &&
                text.length <= 50 &&
                !/\b(h|hr|hrs|hour|hours|d|day|days)\b/i.test(text) &&
                !text.includes("•") &&
                !text.includes("Visible") &&
                !text.match(/^\d+$/)
            ) {
                author = text;
                break;
            }
        }

        /* ================= TIMESTAMP ================= */
        let timestamp = "Unknown";

        const timeAriaSpans = post.querySelectorAll("span[aria-hidden='true']");

        for (const span of timeAriaSpans) {
            const text = span.innerText.replace(/\s+/g, " ").trim();
            const match = text.match(/^(\d+\s?[hdw])/i);
            if (match) {
                timestamp = match[1].replace(" ", "");
                break;
            }
        }

        /* ================= CONTENT ================= */
        let content = "";
        let longestText = "";

        const textSpans = post.querySelectorAll("span[dir='ltr']");

        for (const span of textSpans) {
            const text = span.innerText
                .replace(/\s+\n/g, "\n")
                .replace(/\n+/g, "\n")
                .replace(/\s+/g, " ")
                .trim();

            if (text.length > longestText.length && text.length > 80) {
                longestText = text;
            }
        }

        content = longestText;
        if (!content) return;

        /* ================= EMAIL EXTRACTION ================= */
        let emails = "";

        const emailMatches = content.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi);
        if (emailMatches) {
            const uniqueEmails = [...new Set(
                emailMatches.map(e => e.toLowerCase())
            )];
            emails = uniqueEmails.join(", ");
        }

        /* ================= POST URL ================= */
        let url = "";
        const linkEl = post.querySelector("a[href*='/posts/'], a[href*='/feed/update/']");
        if (linkEl) url = linkEl.href.split("?")[0];

        /* ================= DEDUP ================= */
        const key = url + content.slice(0, 150);
        if (seen.has(key)) return;
        seen.add(key);

        /* ================= JOB CLASSIFICATION ================= */
        const jobKeywords = [
            "hiring",
            "we are hiring",
            "job opening",
            "apply",
            "urgent hiring",
            "looking for",
            "vacancy",
            "open position",
            "send resume",
            "share resume",
            "email your resume",
            "job title"
        ];

        const isJob =
            jobKeywords.some(k => content.toLowerCase().includes(k)) ||
            emails.length > 0;

        // 🚀 Ignore NON-JOB posts completely
        if (!isJob) return;

        results.push({
            author,
            timestamp,
            // post_type: "JOB_POST",
            emails,
            content,
            url
        });
    });

    if (!results.length) {
        alert("No valid posts found. Scroll more and try again.");
        return;
    }

    const csv = convertToCSV(results);
    downloadCSV(csv);
})();

/* ================= CSV HELPERS ================= */

function convertToCSV(data) {
    const headers = Object.keys(data[0]).join(",");
    const rows = data.map(row =>
        Object.values(row)
            .map(v => `"${String(v).replace(/"/g, '""')}"`)
            .join(",")
    );
    return [headers, ...rows].join("\n");
}

function downloadCSV(csv) {
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    chrome.runtime.sendMessage({
        type: "DOWNLOAD_CSV",
        url
    });
}
