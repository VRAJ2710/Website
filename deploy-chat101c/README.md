# deploy-chat101c

A calmer menu and phone market cards, on top of the LIVE chat101b build
(server 27269b06f2e6962a5d5cb56020ca7527, app 29b6f804376fcf50a9cfb262b5f37a30, index 79edd5e9f7966ef8fc3fcf4d0a83f994; c93.css 9d6a86a64135b1cc58e6af7b12973550).

Why: Vraj said the menu was "too much cluster", "not a clear structure", and asked for "the old formate button like full scree structure or a drop down structure".

Run in the project folder (it does not start the server or publish anything):

    bash deploy.sh --dry-run
    bash deploy.sh

What changes (nav and layout only; no routes, data, DB schema or DDL, Stripe, env vars, package.json or .replit):
- "Menu" (below 1280px) and "All sections" (desktop) open the same full-screen sheet. It has a solid background in light and dark, a close X at the top right (aria-label "Close menu"), and closes on Escape or the X with focus going back to the button. The page behind does not scroll while it is open.
- One column of tap-to-expand groups in the old "All sections" label style: Start, Desk, Markets, Research, Book, Gold and macro, Tools and filings, About, Account. Only the current page's group starts open. Headings are real buttons (aria-expanded/aria-controls, 44px).
- "Your desk" (signed in) or "Sign in" sits at the top, and the sign-in note sits small at the bottom. All 36 sections are still linked. Admin Console shows only to the admin, never in guest preview.
- Signed-in pages served from the shared cache now swap every "Sign in" button for "Your desk", not only the first. Before this, /about showed "Sign in" in the phone menu for members.
- The header fits at 320px (it was 355px wide).
- Below 600px, the home and Gold market-context rows become cards. Line 1 is name and value, line 2 is the change (colour and sign kept), and line 3 is source and date (small, muted). They sit under group headings. Every value, change, source, date and Delayed label is kept, and the desktop table is unchanged.

Files:
- `patch_c101c.py`, `server_block_c101c.js` and `app_block_c101c.js` are the patch
- `t_c101c.js` holds the harness tests. `t_c101b.js`, `t_c100_b.js` and `t_c100e.js` have the cache-token regex widened to chat101c
- `audit.js` is the Puppeteer audit (320/390/1280, light/dark, guest/member/admin). `cards.js` and `cards_base.json` hold the market-card counts compared with chat101b
