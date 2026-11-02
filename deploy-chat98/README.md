# chat98 (on chat97): built and tested, not published

The cumulative FINAL deploy.sh on the chat99 branch applies this. Don't run it on its own.

- Alerts `/alerts/` (members): price, level and macro-release alerts, shown in the app and on /alerts/.
  The email path is built but switched OFF (it needs DISPATCH_MAIL_API_KEY, and nothing is ever sent).
- Portfolio X-ray `/portfolio/` (members, for information only): type in holdings by type and amount. It shows
  exposure to growth, the US dollar and gold, plus rate sensitivity, using stated rule-of-thumb assumptions.
  It's not investment advice, and it never uses buy/sell language.
- Tables come from `dev_create.sql`, which you run by hand in the database console (dev first).
  - It uses CREATE TABLE IF NOT EXISTS only (dispatch_alerts, dispatch_alert_events, dispatch_portfolio).
  - There's no DROP or ALTER, so it's safe to run twice.
  - The app never runs DDL itself. It checks the tables with to_regclass and hides both features until they exist.
- Guest preview is read-only, form posts are same-origin only, and maintenance gives a 503.
