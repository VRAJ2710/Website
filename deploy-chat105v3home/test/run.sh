cd /workspace/v3-home-preview/test
(PORT=8787 node harness.js > h1.log 2>&1 &) ; (PORT=8788 BLOCK=0 node harness.js > h0.log 2>&1 &); (PORT=8789 MODE=chunked node harness.js > h2.log 2>&1 &); (PORT=8795 MODE=gzip node harness.js > h3.log 2>&1 &); (PORT=8796 BLOCK=0 MODE=gzip node harness.js > h4.log 2>&1 &); sleep 1.5
