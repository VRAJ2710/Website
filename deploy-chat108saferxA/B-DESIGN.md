# Batch B design (not built): built from the existing Barebone-style v3 components

Order after the hero: desk tabs -> 2. Today's story (split) -> price + gauge strip -> big chart -> 1-2-3 "How to use the desk"
-> more on the home page (Market context table moves under "Market context", Capital Sustainability Monitor) -> closing band.

2. Split story (>= 1000 px): two columns, 5/7. LEFT is `position:sticky` under the header+tabs and holds the existing
   Market Snapshot card (#v3-snap: one-line headline, summary, "updated X min ago", lead story chips) with the gold futures
   chart card (#v3-gold) beneath it. RIGHT scrolls: Market mood (#v3-gauges, horizontal Fear-gauge and 1-year range bars), Key
   prices (#v3-prices), Upcoming events (#v3-cal), What moved (#v3-moves, five bullet rows with kickers). Below 1000 px it
   stacks in reading order: snapshot, mood, prices, chart, events, moved. Done by moving the existing article nodes into two
   wrapper columns in the server transform (no re-render, no new fetches), so every source line and lag label stays.
3. Market identity: Gold #e6b95e (ingot), Dollar #7aa8ff ($ in circle), Yields #a78bfa (percent), Oil #f59e0b (drop),
   Crypto #f97316 (coin), Equities #3fd08f (candles); light-theme variants darkened for AA. Applied as a 3 px top accent and a
   16 px icon in each price tile, chart tile and card kicker by matching the tile's existing label text (Gold spot, Gold in
   pounds, Silver -> Gold group; US dollar index, Pound in dollars -> Dollar; 10-year yield, real yield -> Yields; Brent ->
   Oil; Bitcoin -> Crypto; S&P 500 -> Equities). Up/down colours stay green/red, never the market colour.
4. Section layouts: price + gauge strip = one compact horizontal row of price pills (name, level, coloured % chip, source
   line on a second line) that wraps on phones; big chart = #v3-gold full width at >= 1000 px; then #v3-tiles; a new static
   1-2-3 "How to use the desk" (Read the Brief -> check Mood and Prices -> open Terminal / Calendar), links to real routes only,
   no advice. Duplicate price table: the old "Market context" table (#c93top; rows gold, gold in pounds, dollar index,
   10-year, real yield, bitcoin, WTI) mostly repeats Key prices, but its bitcoin and WTI rows are not in Key prices, so those
   two must move into the price strip before the table can go; its unique "Today's brief" card (#c93brief) stays. Decision needed from Vraj: drop the duplicate table rows or keep them
   collapsed under a "Full table" disclosure (nothing hidden by default) - my recommendation is the disclosure.
5. Big type only in the hero; card headlines 21-25 px sans; data stays at 12-14 px with tabular numerals.
ETA: about 1 working session (3-4 h) to build, plus 1 h QA/screenshots, once Vraj has seen batch A on dev.
