from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask_cors import CORS

app = Flask(__name__)

# Разрешаем запросы с любых источников, включая локальные файлы
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_matrix():
    # Настройка WebDriver
    service = Service('./drivers/chromedriver')
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Открытие новой вкладки через JavaScript
        driver.execute_script("window.open('https://matrix.itasoftware.com', '_blank');")

        # Переключение на новую вкладку
        driver.switch_to.window(driver.window_handles[-1])

        # Установка размера окна
        driver.set_window_size(1792, 1095)

        # Ожидание и клик по полю "Origin"
        origin_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#mat-mdc-form-field-label-0 > .ng-tns-c3899417-0:nth-child(1)"))
        )
        origin_field.click()

        # Ввод текста "GVA"
        input_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mat-mdc-chip-list-input-0"))
        )
        input_element.clear()  # Очищаем поле перед вводом
        input_element.send_keys("GVA")

        # Задержка для обработки выпадающего списка
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".mdc-list-item__primary-text"))
        )

        # Клик по первому варианту из выпадающего списка
        dropdown_item = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".mdc-list-item__primary-text"))
        )
        dropdown_item.click()

    except Exception as e:
        print(f"Произошла ошибка: {e}")

    # Оставляем браузер открытым и завершаем выполнение
    return "Matrix сценарий выполнен! Оставьте вкладку открытой для проверки."

if __name__ == '__main__':
    app.run(debug=True)
