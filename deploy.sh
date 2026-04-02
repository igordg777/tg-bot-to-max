#!/bin/bash
# Деплой лендинга MAXBoты
# Выберите один из вариантов:

SITE_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─── Вариант 1: Surge.sh (бесплатно) ──────────────────────────────────────
# 1. Установите: npm install -g surge
# 2. Укажите ваш токен: export SURGE_TOKEN=<ваш_токен>
# 3. Снимите комментарий и запустите:
# surge "$SITE_DIR" maxboty.surge.sh --token "$SURGE_TOKEN"

# ─── Вариант 2: Netlify CLI ────────────────────────────────────────────────
# 1. Установите: npm install -g netlify-cli
# 2. Залогиньтесь: netlify login
# 3. Снимите комментарий и запустите:
# netlify deploy --dir "$SITE_DIR" --prod

# ─── Вариант 3: GitHub Pages ───────────────────────────────────────────────
# 1. Создайте репозиторий на GitHub
# 2. Настройте remote: git remote add origin https://github.com/ВАШ_ЮЗЕРhttps://github.com/ВАШ_ЮЗЕР/maxboty-landing.git
# 3. Включите GitHub Pages в настройках репозитория (ветка master / корень)
# 4. Снимите комментарий и запустите:
# git -C "$SITE_DIR" remote add origin https://github.com/ВАШ_ЮЗЕР/maxboty-landing.git
# git -C "$SITE_DIR" push -u origin master

echo "Выберите метод деплоя в deploy.sh и запустите соответствующую команду."
echo "Не забудьте заменить YOUR_COUNTER_ID в index.html на ваш реальный ID счётчика Яндекс.Метрики."
