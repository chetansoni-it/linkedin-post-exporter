(function () {
    const MAX_POSTS = 100;

    const posts = [];
    const nodes = document.querySelectorAll("div.feed-shared-update-v2");

    for (let i = 0; i < nodes.length && posts.length < MAX_POSTS; i++) {
        const node = nodes[i];

        const text =
            node.innerText
                ?.replace(/\n+/g, " ")
                ?.replace(/\s+/g, " ")
                ?.trim() || "";

        if (text.length < 50) continue;

        const linkEl = node.querySelector("a[href*='/posts/'], a[href*='/feed/update/']");
        const postUrl = linkEl ? linkEl.href.split("?")[0] : "";

        posts.push({
            content: text,
            url: postUrl
        });
    }

    if (!posts.length) {
        alert("No posts found. Scroll more and try again.");
        return;
    }

    const csv = convertToCSV(posts);
    downloadCSV(csv);
})();

function convertToCSV(data) {
    const headers = Object.keys(data[0]).join(",");
    const rows = data.map(row =>
        Object.values(row)
            .map(v => `"${v.replace(/"/g, '""')}"`)
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
