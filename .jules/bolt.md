## 2026-09-02 - Selenium Headless Optimizations
**Learning:** Disabling image loading and using `eager` page load strategy in Selenium was rejected as it alters fundamental browser capabilities and risks breaking scripts that rely on visual rendering or external resource initialization.
**Action:** Avoid altering core browser settings (like image loading or page load strategies) unless explicitly required; look for algorithmic optimizations, caching, or reducing redundant operations instead.
