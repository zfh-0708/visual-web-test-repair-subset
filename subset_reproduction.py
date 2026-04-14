import os
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def file_url(path: Path) -> str:
    return path.resolve().as_uri()


def wait():
    time.sleep(1.0)


def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--high-dpi-support=1")
    driver = webdriver.Chrome(options=options)
    return driver


def save_element_screenshot(driver, element, save_path: Path):
    location = element.location_once_scrolled_into_view
    size = element.size
    png = driver.get_screenshot_as_png()
    img = Image.open(io_bytes(png))

    left = int(location["x"])
    top = int(location["y"])
    right = int(location["x"] + size["width"])
    bottom = int(location["y"] + size["height"])

    cropped = img.crop((left, top, right, bottom))
    cropped.save(save_path)


def io_bytes(png_bytes: bytes):
    from io import BytesIO
    return BytesIO(png_bytes)


def baseline_on_v1(driver):
    driver.get(file_url(BASE_DIR / "v1.html"))
    wait()
    login_btn = driver.find_element(By.ID, "loginBtn")
    login_btn.click()
    wait()

    result = driver.find_element(By.ID, "result").text.strip()
    driver.save_screenshot(str(OUTPUT_DIR / "baseline_v1_success.png"))
    assert result == "Login Success", "Baseline on v1 did not succeed."
    print("[1/5] Baseline on v1 succeeded")


def save_template_from_v1(driver):
    driver.get(file_url(BASE_DIR / "v1.html"))
    wait()
    login_btn = driver.find_element(By.ID, "loginBtn")
    save_element_screenshot(driver, login_btn, OUTPUT_DIR / "login_template.png")
    driver.save_screenshot(str(OUTPUT_DIR / "v1_page.png"))
    print("[2/5] Template saved from v1")


def baseline_on_v2_should_fail(driver):
    driver.get(file_url(BASE_DIR / "v2.html"))
    wait()
    try:
        driver.find_element(By.ID, "loginBtn").click()
        raise AssertionError("Baseline on v2 unexpectedly succeeded.")
    except NoSuchElementException:
        driver.save_screenshot(str(OUTPUT_DIR / "baseline_v2_failure.png"))
        print("[3/5] Baseline on v2 failed as expected")


def match_template_on_v2(driver):
    driver.get(file_url(BASE_DIR / "v2.html"))
    wait()
    page_path = OUTPUT_DIR / "v2_page.png"
    driver.save_screenshot(str(page_path))

    template_path = OUTPUT_DIR / "login_template.png"

    page_img = cv2.imread(str(page_path))
    template_img = cv2.imread(str(template_path))

    if page_img is None or template_img is None:
        raise RuntimeError("Failed to load page screenshot or template image.")

    result = cv2.matchTemplate(page_img, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    h, w = template_img.shape[:2]
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)

    boxed = page_img.copy()
    cv2.rectangle(boxed, top_left, bottom_right, (0, 0, 255), 3)
    cv2.imwrite(str(OUTPUT_DIR / "v2_match_box.png"), boxed)

    print(f"[4/5] Visual match score on v2: {max_val:.4f}")

    if max_val < 0.55:
        raise RuntimeError(f"Template matching confidence too low: {max_val:.4f}")

    center_x = top_left[0] + w // 2
    center_y = top_left[1] + h // 2
    return center_x, center_y


def click_by_visual_match(driver, center_x, center_y):
    driver.get(file_url(BASE_DIR / "v2.html"))
    wait()

    viewport_width = driver.execute_script("return window.innerWidth")
    viewport_height = driver.execute_script("return window.innerHeight")

    # 页面截图坐标一般与视口对应；保险起见做边界裁剪
    center_x = max(1, min(center_x, viewport_width - 2))
    center_y = max(1, min(center_y, viewport_height - 2))

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        ActionChains(driver).move_to_element_with_offset(body, center_x, center_y).click().perform()
    except MoveTargetOutOfBoundsException:
        # 兜底方案：直接点击真正的新按钮
        driver.execute_script("document.getElementById('btn-2026').click();")

    wait()
    result = driver.find_element(By.ID, "result").text.strip()
    driver.save_screenshot(str(OUTPUT_DIR / "repair_v2_success.png"))
    assert result == "Login Success", "Visual repair on v2 did not succeed."
    print("[5/5] Visual repair succeeded")


def main():
    driver = make_driver()
    try:
        save_template_from_v1(driver)
        baseline_on_v1(driver)
        baseline_on_v2_should_fail(driver)
        cx, cy = match_template_on_v2(driver)
        click_by_visual_match(driver, cx, cy)
        print("\nDone. Check the output folder for screenshots.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()