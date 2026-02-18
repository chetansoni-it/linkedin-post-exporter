/**
 * ============================================
 *  Configuration File
 *  Change these values as needed.
 * ============================================
 */
const CONFIG = Object.freeze({

    // ---- API Settings ----
    API_BASE_URL: "http://localhost:8000",   // Backend API base URL
    API_ENDPOINT: "/posts",                  // Endpoint path to send post data
    API_TIMEOUT_MS: 10000,                   // Timeout per batch request (ms)

    // ---- Batch Settings ----
    BATCH_SIZE: 10,                          // Number of posts per batch sent to API
    BATCH_DELAY_MS: 500,                     // Delay between consecutive batches (ms)

    // ---- Feature Toggles ----
    ENABLE_API_SEND: true,                   // Set to false to disable API sending entirely
});
