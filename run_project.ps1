# Проверяем наличие Python
Write-Host "Проверка наличия Python..."
if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Host "Python не установлен. Пожалуйста, установите Python 3.7+ и добавьте его в PATH."
    exit
}

# Создаем виртуальное окружение
Write-Host "Создание виртуального окружения..."
if (-not (Test-Path "venv")) {
    python3 -m venv venv
}

# Активируем виртуальное окружение
Write-Host "Активируем виртуальное окружение..."
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1

# Проверяем и устанавливаем необходимые библиотеки
Write-Host "Проверка и установка необходимых библиотек..."
# $requiredPackages = @("flask", "selenium", "flask-cors")
$requiredPackages = @("flask", "flask-cors", "Flask[async]", "playwright")
foreach ($package in $requiredPackages) {
    $isInstalled = pip show $package -q
    if (-not $isInstalled) {
        Write-Host "Установка $package..."
        pip install $package
    } else {
        Write-Host "$package уже установлен."
    }
}

# Проверяем наличие проекта и обновляем из Git
Write-Host "Проверка наличия проекта..."
if (-not (Test-Path "matrix-ita")) {
    Write-Host "Клонирование проекта из Git..."
    git clone https://github.com/MaxShytov/matrix-ita.git
} else {
    Write-Host "Обновление проекта из Git..."
    Set-Location matrix-ita
    git pull origin main
    Set-Location ..
}

# Запуск проекта
Write-Host "Запуск проекта..."
Set-Location matrix-ita
python app.py
