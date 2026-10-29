I’ll retrieve the current `frontend/src/index.js` and provide the complete entry-point file.
Action: view_file({"path":"/app/frontend/src/index.js","view_range":[1,1000]})
Observation: [Showing lines 1-24 of 24 total] /app/frontend/src/index.js:
1|import React from "react";
2|import ReactDOM from "react-dom/client";
3|import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
4|import "@/index.css";
5|import App from "@/App";
6|
7|const queryClient = new QueryClient({
8|  defaultOptions: {
9|    queries: {
10|      staleTime: 60_000,
11|      refetchOnWindowFocus: false,
12|    },
13|  },
14|});
15|
16|const root = ReactDOM.createRoot(document.getElementById("root"));
17|root.render(
18|  <React.StrictMode>
19|    <QueryClientProvider client={queryClient}>
20|      <App />
21|    </QueryClientProvider>
22|  </React.StrictMode>,
23|);
24|
[End of file]
