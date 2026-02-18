chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "DOWNLOAD_CSV") {
        chrome.downloads.download({
            url: msg.url,
            filename: "linkedin_posts.csv"
        });
    }
});
