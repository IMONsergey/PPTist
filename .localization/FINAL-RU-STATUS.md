# PPTist Russian localization status

- User-facing source UI: Russian; Chinese Han remains only in developer comments.
- Shipped `public` textual assets: zero Chinese Han text.
- Shipped demo/template/AI JSON and Markdown content: translated to Russian.
- ECharts runtime: explicitly initialized with the Russian locale object.
- Production Vite build: passed.
- Vue/TypeScript type-check: passed.
- Built non-JS user-facing textual assets: zero Chinese Han text.
- ECharts may still physically bundle its unused Chinese locale dictionary and CJK width probe inside vendor JavaScript; runtime charts use the explicit Russian locale.
