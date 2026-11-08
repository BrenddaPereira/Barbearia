async def run_test(page, output_dir, page_url):
    import traceback
    try:
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.goto("https://barbearia-carille.preview.emergentagent.com", wait_until="networkidle", timeout=30000)
        await page.wait_for_selector('[data-testid="hero-book-button"]', timeout=10000)
        print("PASS: homepage loaded")
        await page.locator('[data-testid="hero-book-button"]').scroll_into_view_if_needed()
        await page.locator('[data-testid="hero-book-button"]').click()
        await page.wait_for_selector('[data-testid="booking-modal"]', timeout=5000)
        print("PASS: booking modal opened")
        await page.locator('[data-testid="booking-next-service"]').click()
        await page.wait_for_selector('[data-testid="booking-next-time"]', timeout=5000)
        dates = await page.locator('[data-testid^="booking-date-"]').all()
        await dates[-1].scroll_into_view_if_needed()
        await dates[-1].click()
        await page.locator('[data-testid="booking-time-18:00"]').scroll_into_view_if_needed()
        await page.locator('[data-testid="booking-time-18:00"]').click()
        await page.locator('[data-testid="booking-next-time"]').click()
        await page.wait_for_selector('[data-testid="booking-name-input"]', timeout=5000)
        await page.locator('[data-testid="booking-name-input"]').fill("TEST Mobile Final")
        await page.locator('[data-testid="booking-phone-input"]').fill("11988887777")
        await page.locator('[data-testid="booking-confirm-button"]').scroll_into_view_if_needed()
        await page.locator('[data-testid="booking-confirm-button"]').click()
        await page.wait_for_selector('[data-testid="booking-confirmation"]', timeout=15000)
        print("PASS: booking submitted and confirmation shown")
        error_text = await page.evaluate("""() => { const errorElements = Array.from(document.querySelectorAll('.error, [class*='error'], [id*='error']')); return errorElements.map(el => el.textContent).join(', '); }""")
        if error_text:
            print(f"Found error message: {error_text}")
        else:
            print("No error messages found on the page")
    except Exception as exc:
        print("FINDING: UI flow failed: " + str(exc))
        traceback.print_exc()

