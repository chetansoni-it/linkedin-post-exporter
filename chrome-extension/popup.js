document.addEventListener("DOMContentLoaded", () => {
    const status = document.getElementById("status");
    const limitInput = document.getElementById("limit");

    async function getActiveLinkedInTab() {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab || !tab.url.includes("linkedin.com")) return null;
        return tab;
    }

    // 🔹 Manual export (no scroll)
    document.getElementById("exportVisible").onclick = async () => {
        const tab = await getActiveLinkedInTab();
        if (!tab) {
            status.innerText = "Open LinkedIn page first";
            return;
        }

        chrome.tabs.sendMessage(tab.id, {
            type: "EXPORT_VISIBLE"
        });

        status.innerText = "Exporting visible posts...";
    };

    // 🔹 Auto scroll + export
    document.getElementById("startScan").onclick = async () => {
        const tab = await getActiveLinkedInTab();
        if (!tab) {
            status.innerText = "Open LinkedIn page first";
            return;
        }

        const limit = parseInt(limitInput.value, 10) || 100;

        chrome.tabs.sendMessage(tab.id, {
            type: "START_SCAN",
            limit
        });

        status.innerText = `Auto scanning ${limit} posts...`;
    };
});
