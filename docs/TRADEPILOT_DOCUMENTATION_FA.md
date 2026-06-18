# مستندات کامل TradePilot AI

## 1. معرفی پروژه

TradePilot AI در وضعیت فعلی یک محیط کامل **Development برای Paper Trading** است. هدف این نسخه، تست جریان تحلیل بازار، امتیازدهی GPT، کنترل ریسک، باز و بسته شدن موقعیت مجازی و محاسبه PnL بدون استفاده از سرمایه واقعی است.

این نسخه:

- هیچ سفارش واقعی ثبت نمی‌کند.
- به endpointهای سفارش صرافی متصل نیست.
- بخش Bitunix، API Key و Live Trading از برنامه حذف شده است.
- از PostgreSQL برای ذخیره داده‌ها استفاده می‌کند.
- از Mock Market Data برای تولید قیمت و کندل استفاده می‌کند.
- دارای frontend با Next.js و backend با Flask است.
- دارای worker مستقل برای مانیتور مداوم قیمت و موقعیت‌ها است.

> هشدار: تمام معاملات، قیمت‌ها و سود و زیان این نسخه شبیه‌سازی شده‌اند. هیچ نتیجه‌ای تضمین‌کننده سود در بازار واقعی نیست.

## 2. وضعیت فعلی

قابلیت‌های پیاده‌سازی‌شده:

- ثبت‌نام و ورود با username و password
- JWT authentication و logout با token blocklist
- ساخت خودکار اشتراک Development
- فعال‌سازی خودکار Paper Bot
- حساب مجازی با موجودی اولیه 10,000 USDT
- تولید کندل‌های OHLCV شبیه‌سازی‌شده
- محاسبه EMA50، EMA200، RSI14 و ATR14
- تولید سیگنال LONG، SHORT یا HOLD
- GPT Confidence Layer اختیاری
- کنترل ریسک و position sizing
- موقعیت‌های مجازی، TP، SL و بستن دستی
- محاسبه realized و unrealized PnL
- تاریخچه معاملات و سیگنال‌ها
- worker دائمی با tick دوثانیه‌ای
- تحلیل Strategy/GPT هر 30 ثانیه
- داشبورد متصل به API واقعی backend
- Docker Compose برای frontend، backend، worker و PostgreSQL

## 3. اطلاعات ورود Development

در حالت Development فقط credential تنظیم‌شده پذیرفته می‌شود:

```text
Username: ilyanozary
Password: ilyalm10
```

در اولین ثبت‌نام، backend به‌صورت خودکار موارد زیر را ایجاد می‌کند:

- کاربر Development
- اشتراک فعال بلندمدت
- Bot Profile با حالت `paper`
- Bot با وضعیت روشن
- حساب Paper با 10,000 USDT

اگر کاربر قبلا ثبت شده باشد، frontend به‌صورت خودکار login را امتحان می‌کند.

## 4. معماری سیستم

```text
Browser / Next.js
        |
        | HTTP + JWT
        v
Flask REST API ---------------- PostgreSQL
        |
        +---- Strategy Engine
        |
        +---- GPT Risk Filter (optional)
        |
        +---- Paper Execution Engine
        |
        +---- Mock Market Data

Independent Paper Worker
        |
        +---- Price tick every 2 seconds
        +---- Strategy/GPT analysis every 30 seconds
        +---- TP/SL monitoring
```

### سرویس‌های Docker

| سرویس | وظیفه | پورت |
|---|---|---:|
| `frontend` | رابط Next.js و hot reload | 3000 |
| `backend` | Flask API و migration | 5000 |
| `paper-worker` | مانیتور دائمی Paper Bot | ندارد |
| `postgres` | دیتابیس PostgreSQL | 5432 |

## 5. ساختار پروژه

```text
app/
  __init__.py
  config.py
  extensions.py
  cli.py
  models/
    user.py
    subscription.py
    payment.py
    bot_profile.py
    paper_account.py
    paper_position.py
    paper_trade.py
    paper_signal.py
    token_blocklist.py
  routes/
    auth.py
    user.py
    subscription.py
    payment.py
    admin.py
    bot.py
    paper.py
    dashboard.py
  services/
    market_data_service.py
    strategy_engine.py
    ai_signal_service.py
    paper_trading_engine.py
    payment_service.py
    subscription_service.py
  dashboard/
    page.tsx
    bot/page.tsx
    positions/page.tsx
    history/page.tsx
    settings/page.tsx
components/
lib/
  api.ts
migrations/
tests/
docker/
docker-compose.yml
Dockerfile.frontend.dev
Dockerfile.backend.dev
```

## 6. راه‌اندازی با Docker

### ساخت فایل environment

```bash
cp .env.example .env
```

برای Development حداقل مقادیر زیر کافی است:

```env
SECRET_KEY=یک-مقدار-تصادفی-طولانی
JWT_SECRET_KEY=یک-مقدار-تصادفی-طولانی-دیگر
DEVELOPMENT_MODE=true
DEV_USERNAME=ilyanozary
DEV_PASSWORD=ilyalm10
MARKET_DATA_PROVIDER=mock
OPENAI_API_KEY=
```

برای داده واقعی فیوچرز Bitunix مقدار `MARKET_DATA_PROVIDER=bitunix` را قرار دهید. Paper Trading همچنان کاملا مجازی می‌ماند و خطای Bitunix هیچ‌وقت مخفیانه با mock جایگزین نمی‌شود. کلیدهای حساب در Settings به‌صورت رمزگذاری‌شده ذخیره می‌شوند. سفارش واقعی نیز در سطح سرور با `LIVE_TRADING_API_ENABLED=false` به‌صورت پیش‌فرض قفل است.

ساخت secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### اجرای تمیز با دیتابیس خالی

این دستور volume قبلی PostgreSQL را حذف می‌کند:

```bash
sudo docker compose down -v --remove-orphans
sudo docker compose up --build
```

آدرس‌ها:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:5000
Postgres: localhost:5432
```

### اجرای پس‌زمینه

```bash
sudo docker compose up -d --build
```

### مشاهده لاگ‌ها

تمام سرویس‌ها:

```bash
sudo docker compose logs -f
```

فقط backend و worker:

```bash
sudo docker compose logs -f backend paper-worker
```

لاگ worker:

```text
[paper-worker] tick user=1 symbol=SOLUSDT price=... positions=1 equity=...
[paper-worker] analysis user=1 strategy=LONG base=85 gpt=LONG:80 opened=True reason=...
```

### Restart بعد از تغییر کد

به دلیل source volume، Flask و Next دارای hot reload هستند. برای تغییرات worker:

```bash
sudo docker compose restart paper-worker
```

برای rebuild وابستگی‌ها یا Dockerfile:

```bash
sudo docker compose up -d --build frontend backend paper-worker
```

## 7. اجرای بدون Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app run.py db upgrade
flask --app run.py run --debug --port 5000
```

در ترمینال دیگر:

```bash
npm install
NEXT_PUBLIC_API_URL=http://localhost:5000 npm run dev
```

worker محلی:

```bash
flask --app run.py paper-engine run-worker --tick-seconds 2 --analysis-seconds 30
```

## 8. جریان احراز هویت

### ثبت‌نام

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "ilyanozary",
  "password": "ilyalm10",
  "full_name": "Ilya Nozary"
}
```

پاسخ شامل `access_token` و اطلاعات کاربر است. frontend توکن را در `localStorage` با کلید `tradepilot_token` ذخیره می‌کند.

### ورود

```http
POST /api/auth/login

{
  "username": "ilyanozary",
  "password": "ilyalm10"
}
```

### دریافت کاربر جاری

```http
GET /api/auth/me
Authorization: Bearer ACCESS_TOKEN
```

### خروج

```http
POST /api/auth/logout
Authorization: Bearer ACCESS_TOKEN
```

توکن logout شده در جدول `token_blocklist` ذخیره و باطل می‌شود.

## 9. بازارهای Paper Trading

نمادهای فعلی:

| نماد | پروفایل نوسان Mock |
|---|---|
| `BTCUSDT` | پایین‌تر و کنترل‌شده‌تر |
| `ETHUSDT` | متوسط |
| `SOLUSDT` | متوسط رو به بالا |
| `DOGEUSDT` | بالا |
| `AVAXUSDT` | بالا |
| `LINKUSDT` | متوسط رو به بالا |

نوسان بالاتر صرفا برای تست بهتر TP/SL، PnL و رفتار engine است و معنای فرصت سود تضمینی ندارد.

## 10. Market Data Service

فایل اصلی:

```text
app/services/market_data_service.py
```

هر کندل شامل موارد زیر است:

```json
{
  "open": 100.0,
  "high": 102.0,
  "low": 99.0,
  "close": 101.0,
  "volume": 1250.0,
  "timestamp": "2026-06-12T12:00:00+00:00"
}
```

قیمت live mock با موج کوتاه‌مدت زمانی تغییر می‌کند تا frontend هر دو ثانیه حرکت قیمت را نمایش دهد.

## 11. Strategy Engine

فایل:

```text
app/services/strategy_engine.py
```

اندیکاتورها:

- EMA 50
- EMA 200
- RSI 14
- ATR 14
- حجم فعلی نسبت به میانگین 20 کندل

### قانون LONG

```text
EMA50 > EMA200
Price > EMA50
50 <= RSI14 <= 70
```

### قانون SHORT

```text
EMA50 < EMA200
Price < EMA50
30 <= RSI14 <= 50
```

در غیر این صورت خروجی `HOLD` است.

### Stop Loss و Take Profit

LONG:

```text
SL = Entry - ATR
TP = Entry + 2 * ATR
```

SHORT:

```text
SL = Entry + ATR
TP = Entry - 2 * ATR
```

### Confidence پایه

امتیاز از 50 شروع می‌شود:

- تطابق روند EMA: `+15`
- تطابق قیمت: `+15`
- تطابق RSI: `+15`
- حجم بالاتر از میانگین: `+10`
- حداکثر امتیاز: `85`

امتیاز LONG و SHORT همیشه جداگانه و به‌صورت پیوسته محاسبه می‌شود. قدرت فاصله EMA50 و EMA200 نسبت به ATR، فاصله قیمت از EMA50، جایگاه RSI داخل بازه معتبر و نسبت حجم به میانگین روی امتیاز اثر می‌گذارند. بنابراین حتی دو setup که هر سه شرط را پاس کرده‌اند لزوما confidence یکسان ندارند. اگر هیچ سمت تمام شروط لازم را پاس نکند، action برابر HOLD می‌ماند، اما confidence دیگر روی 50 ثابت نیست و کیفیت نزدیک‌ترین setup نمایش داده می‌شود. این امتیاز به‌تنهایی اجازه اجرا نمی‌دهد، چون برای بازشدن معامله همچنان تمام شروط جهت انتخاب‌شده باید پاس شوند.

## 12. GPT Confidence Layer

فایل:

```text
app/services/ai_signal_service.py
```

اگر `OPENAI_API_KEY` خالی باشد:

```json
{
  "action": "LONG",
  "confidence": 75,
  "ai_reason": "AI disabled; using rule-based strategy confidence."
}
```

اگر API Key تنظیم شده باشد، GPT فقط risk filter است:

- اجازه ساخت جهت جدید ندارد.
- LONG را فقط می‌تواند LONG یا HOLD کند.
- SHORT را فقط می‌تواند SHORT یا HOLD کند.
- HOLD را باید HOLD نگه دارد.
- confidence GPT نمی‌تواند بیشتر از confidence strategy باشد.
- پاسخ مخالف strategy به HOLD با confidence صفر تبدیل می‌شود.
- خطای API یا JSON باعث fallback به امتیاز strategy می‌شود.

GPT هیچ‌گاه risk ruleها را دور نمی‌زند.

## 13. Risk Management و Position Sizing

پیش از باز شدن موقعیت:

- Bot باید در حالت `paper` باشد.
- Bot باید روشن باشد.
- action باید LONG یا SHORT باشد.
- confidence باید از threshold عبور کند.
- برای همان user/symbol نباید موقعیت باز دیگری وجود داشته باشد.
- موجودی آزاد باید مثبت باشد.
- SL و TP باید با جهت موقعیت سازگار باشند.
- risk percentage باید معتبر باشد.

فرمول اندازه موقعیت:

```text
risk_amount = balance * risk_per_trade_percent / 100
stop_distance = abs(entry_price - stop_loss)
quantity = risk_amount / stop_distance
margin = quantity * entry_price / leverage
```

اگر margin بیشتر از موجودی آزاد باشد، quantity کاهش می‌یابد.

## 14. حساب و PnL

### مقایسه سناریوی LONG و SHORT

هر بار که تحلیل کامل اجرا می‌شود، backend علاوه بر سیگنال اصلی دو سناریوی فرضی تولید می‌کند. این سناریوها سفارش باز نمی‌کنند و فقط پاسخ می‌دهند که اگر در همان لحظه LONG یا SHORT گرفته می‌شد چه پارامترهایی داشت:

- تعداد شروط تکنیکال پاس‌شده
- confidence هر سمت
- entry، stop loss و take profit
- quantity و margin فرضی
- حداکثر ریسک دلاری
- سود هدف با نسبت ریسک به بازده 1:2
- eligible یا blocked بودن سناریو
- PnL فرضی زنده نسبت به قیمت فعلی

پنل `What-If Scenario Comparison` در صفحه Paper Engine هر دو سمت را کنار هم نمایش می‌دهد. PnL این پنل با tick دوثانیه‌ای تغییر می‌کند، اما هیچ‌کدام از این دو سناریو صرفا به دلیل نمایش در پنل اجرا نمی‌شوند.

### تعریف مقادیر

- `balance_usdt`: موجودی آزاد
- `margin_usdt`: سرمایه مجازی قفل‌شده در موقعیت
- `unrealized_pnl`: سود و زیان موقعیت‌های باز
- `realized_pnl`: سود و زیان معاملات بسته‌شده
- `equity_usdt`: موجودی آزاد + margin قفل‌شده + PnL شناور

### PnL لانگ

```text
pnl = (current_price - entry_price) * quantity
```

### PnL شورت

```text
pnl = (entry_price - current_price) * quantity
```

هنگام بسته شدن:

```text
balance += margin + pnl
realized_pnl += pnl
```

## 15. Worker دائمی

Worker از command زیر استفاده می‌کند:

```bash
flask --app run.py paper-engine run-worker --tick-seconds 2 --analysis-seconds 30
```

عملکرد:

1. Bot Profileهای روشن و Paper را می‌خواند.
2. هر دو ثانیه قیمت را به‌روزرسانی می‌کند.
3. PnL موقعیت‌های باز را محاسبه می‌کند.
4. TP و SL را بررسی می‌کند.
5. هر 30 ثانیه Strategy و GPT را اجرا می‌کند.
6. اگر risk check پاس شود موقعیت مجازی باز می‌کند.
7. نتیجه را در stdout چاپ می‌کند.

وضعیت روشن Bot در دیتابیس ذخیره شده و با reload یا بسته‌شدن مرورگر از بین نمی‌رود. Worker مستقل از frontend ادامه می‌دهد.

## 16. Paper Trading API

تمام endpointها به‌جز auth نیازمند JWT هستند. endpointهای تغییر وضعیت و engine به اشتراک فعال نیاز دارند.

### حساب

```text
GET  /api/paper/account
POST /api/paper/account/reset
```

### موقعیت‌ها

```text
GET  /api/paper/positions
POST /api/paper/positions/open
POST /api/paper/positions/:id/close
```

نمونه بازکردن دستی:

```json
{
  "symbol": "SOLUSDT",
  "side": "LONG",
  "entry_price": 150,
  "stop_loss": 147,
  "take_profit": 156,
  "margin_usdt": 100,
  "leverage": 1,
  "confidence": 75
}
```

### معاملات و سیگنال‌ها

```text
GET /api/paper/trades
GET /api/paper/signals
```

### Engine

```text
POST /api/paper/engine/run-once
POST /api/paper/engine/tick
```

`run-once` یک تحلیل کامل Strategy/GPT/Risk انجام می‌دهد.

`tick` فقط قیمت، PnL، TP/SL و account totals را به‌روزرسانی می‌کند و برای polling سریع frontend مناسب است.

نمونه پاسخ `run-once`:

```json
{
  "success": true,
  "mode": "paper",
  "symbol": "SOLUSDT",
  "strategy_signal": {
    "action": "LONG",
    "confidence_base": 85
  },
  "ai_signal": {
    "action": "LONG",
    "confidence": 80,
    "ai_reason": "Signal confirmed conservatively."
  },
  "position_opened": true,
  "reason": "Virtual paper position opened"
}
```

## 17. سایر APIها

### Bot Profile

```text
GET   /api/bot/profile
POST  /api/bot/profile
PATCH /api/bot/profile
```

فقط mode برابر `paper` پذیرفته می‌شود.

### Dashboard

```text
GET /api/dashboard/overview
```

خروجی شامل موارد زیر است:

- paper balance
- paper equity
- realized PnL
- unrealized PnL
- تعداد موقعیت‌های باز
- آخرین معاملات
- آخرین سیگنال‌های GPT-filtered

### Subscription و Payment

زیرساخت اولیه اشتراک و پرداخت USDT هنوز در backend وجود دارد:

```text
GET  /api/subscriptions/plans
GET  /api/subscriptions/current
POST /api/payments/create
GET  /api/payments/:id
POST /api/payments/:id/submit-tx
GET  /api/admin/payments
POST /api/admin/payments/:id/confirm
POST /api/admin/payments/:id/reject
```

در UI فعلی Development از این جریان استفاده نمی‌شود؛ ثبت‌نام اشتراک Development را خودکار می‌سازد.

## 18. مدل‌های دیتابیس

### User

- username
- email اختیاری
- password hash
- full name
- role
- active status

### BotProfile

- mode: فقط paper
- risk profile
- symbol
- enabled status
- confidence threshold
- max daily loss percent
- risk per trade percent

### PaperAccount

- balance
- equity
- realized PnL
- unrealized PnL

### PaperPosition

- symbol و side
- entry/current price
- quantity و margin
- leverage
- SL و TP
- confidence
- status
- close details
- PnL

### PaperTrade

نسخه نهایی و immutable معامله بسته‌شده، شامل دلیل خروج و توضیح GPT.

### PaperSignal

سیگنال Strategy/GPT شامل action، confidence، قیمت‌ها، دلایل و وضعیت executed.

## 19. Migrationها

ترتیب migrationهای فعلی:

```text
8f8e4d74ffd0  initial schema
b005620d49fe  paper trading tables
1ea50a500b9c  username authentication
d7e2a9104c31  remove exchange API keys
```

اعمال migration:

```bash
flask --app run.py db upgrade
```

مشاهده revision:

```bash
flask --app run.py db current
```

در Docker، backend entrypoint migration را خودکار اجرا می‌کند.

## 20. صفحات frontend

| مسیر | کاربرد |
|---|---|
| `/` | ثبت‌نام و ورود Development |
| `/dashboard` | موجودی، equity، PnL، سیگنال‌ها و معاملات |
| `/dashboard/bot` | کنترل Bot، قیمت سریع، Strategy/GPT/Risk pipeline |
| `/dashboard/positions` | موقعیت‌های باز/بسته و بستن دستی |
| `/dashboard/history` | تاریخچه معاملات و GPT reason |
| `/dashboard/settings` | اطلاعات کاربر و reset حساب Paper |

## 21. تست‌ها

اجرای تست:

```bash
source .venv/bin/activate
python -m unittest discover -v
```

پوشش فعلی شامل:

- fallback بدون GPT
- تولید بازار برای تمام شش نماد
- bootstrap ثبت‌نام Development
- اجرای engine و بازکردن موقعیت
- JWT protection
- manual open
- PnL و بستن دستی
- TAKE_PROFIT خودکار
- tick قیمت و account

آخرین وضعیت ثبت‌شده: **9 تست پاس**.

Production build frontend:

```bash
NEXT_DIST_DIR=.next-local npm run build
```

## 22. رفع خطاهای رایج

### پورت 5000 اشغال است

```text
failed to bind host port 0.0.0.0:5000: address already in use
```

بررسی:

```bash
sudo ss -ltnp | grep ':5000'
```

متوقف‌کردن Flask محلی یا کانتینر قدیمی:

```bash
sudo docker compose down --remove-orphans
```

### دسترسی Docker denied

```text
permission denied while trying to connect to docker.sock
```

اجرای موقت:

```bash
sudo docker compose up --build
```

رفع دائمی:

```bash
sudo usermod -aG docker $USER
```

سپس logout/login کنید.

### پاک‌کردن کامل دیتابیس Docker

```bash
sudo docker compose down -v
```

این دستور تمام داده‌های PostgreSQL را حذف می‌کند.

### مشاهده نشدن نماد یا تغییر جدید

```bash
sudo docker compose restart frontend backend paper-worker
```

اگر dependency یا image تغییر کرده است:

```bash
sudo docker compose up -d --build
```

### خطای permission در `.next`

Compose فعلی `.next` را در volume جداگانه نگه می‌دارد. برای build محلی از مسیر مستقل استفاده کنید:

```bash
NEXT_DIST_DIR=.next-local npm run build
```

## 23. امنیت و محدودیت‌ها

موارد موجود:

- password hashing با Werkzeug
- JWT access token
- token revocation در logout
- validation با Marshmallow
- role protection برای admin endpoints
- subscription protection برای engine
- CORS از environment
- محاسبات مالی دیتابیس با Numeric/Decimal

محدودیت‌های فعلی:

- credential Development ثابت است.
- token در localStorage نگهداری می‌شود؛ برای production بهتر است HttpOnly cookie استفاده شود.
- rate limiting وجود ندارد.
- email verification و password recovery وجود ندارد.
- GPT API اختیاری است و بدون key از strategy fallback استفاده می‌شود.
- داده بازار واقعی نیست.
- slippage، fee، funding و liquidation مدل‌سازی نشده‌اند.
- worker فعلی single-process polling است و برای scale بالا باید queue/scheduler اضافه شود.
- پرداخت در UI Development فعال نیست.

## 24. مسیر پیشنهادی ادامه توسعه

1. اضافه‌کردن fee، slippage و funding به شبیه‌سازی
2. ساخت equity curve واقعی از snapshots
3. اضافه‌کردن daily loss lock و max concurrent positions
4. اضافه‌کردن refresh token و HttpOnly cookies
5. اضافه‌کردن rate limiting و audit log
6. اضافه‌کردن تست‌های PostgreSQL و integration تست Docker
7. اتصال فقط-read به provider داده بازار واقعی
8. ساخت صفحه تنظیم confidence، risk و analysis interval
9. اضافه‌کردن backtesting جدا از paper runtime
10. بررسی امنیت مستقل پیش از هرگونه Live Trading

## 25. خلاصه عملیاتی

اجرای کامل و تمیز:

```bash
cd /home/ilya/Documents/trading_copilet
cp .env.example .env
sudo docker compose down -v --remove-orphans
sudo docker compose up --build
```

ورود:

```text
http://localhost:3000
ilyanozary / ilyalm10
```

مشاهده worker:

```bash
sudo docker compose logs -f paper-worker backend
```

خاموش‌کردن:

```bash
sudo docker compose down
```

حذف کامل داده‌ها:

```bash
sudo docker compose down -v
```

این نسخه برای مشاهده و تست شفاف جریان Paper Trading آماده است، اما برای معامله واقعی طراحی یا تایید نشده است.
