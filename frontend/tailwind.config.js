I’ll retrieve the current `frontend/tailwind.config.js` and provide the complete configuration file.
Action: view_file({"path":"/app/frontend/tailwind.config.js","view_range":[1,1000]})
Observation: [Showing lines 1-84 of 84 total] /app/frontend/tailwind.config.js:
1|/** @type {import('tailwindcss').Config} */
2|module.exports = {
3|    // `overline` is a Tailwind utility; without this an app's own eyebrow-label class draws a line above the text.
4|    blocklist: ["overline"],
5|    darkMode: ["class"],
6|    content: [
7|    "./src/**/*.{js,jsx,ts,tsx}",
8|    "./public/index.html"
9|  ],
10|  theme: {
11|    extend: {
12|      borderRadius: {
13|        lg: 'var(--radius)',
14|        md: 'calc(var(--radius) - 2px)',
15|        sm: 'calc(var(--radius) - 4px)'
16|      },
17|      colors: {
18|        background: 'hsl(var(--background))',
19|        foreground: 'hsl(var(--foreground))',
20|        card: {
21|          DEFAULT: 'hsl(var(--card))',
22|          foreground: 'hsl(var(--card-foreground))'
23|        },
24|        popover: {
25|          DEFAULT: 'hsl(var(--popover))',
26|          foreground: 'hsl(var(--popover-foreground))'
27|        },
28|        primary: {
29|          DEFAULT: 'hsl(var(--primary))',
30|          foreground: 'hsl(var(--primary-foreground))'
31|        },
32|        secondary: {
33|          DEFAULT: 'hsl(var(--secondary))',
34|          foreground: 'hsl(var(--secondary-foreground))'
35|        },
36|        muted: {
37|          DEFAULT: 'hsl(var(--muted))',
38|          foreground: 'hsl(var(--muted-foreground))'
39|        },
40|        accent: {
41|          DEFAULT: 'hsl(var(--accent))',
42|          foreground: 'hsl(var(--accent-foreground))'
43|        },
44|        destructive: {
45|          DEFAULT: 'hsl(var(--destructive))',
46|          foreground: 'hsl(var(--destructive-foreground))'
47|        },
48|        border: 'hsl(var(--border))',
49|        input: 'hsl(var(--input))',
50|        ring: 'hsl(var(--ring))',
51|        chart: {
52|          '1': 'hsl(var(--chart-1))',
53|          '2': 'hsl(var(--chart-2))',
54|          '3': 'hsl(var(--chart-3))',
55|          '4': 'hsl(var(--chart-4))',
56|          '5': 'hsl(var(--chart-5))'
57|        }
58|      },
59|      keyframes: {
60|        'accordion-down': {
61|          from: {
62|            height: '0'
63|          },
64|          to: {
65|            height: 'var(--radix-accordion-content-height)'
66|          }
67|        },
68|        'accordion-up': {
69|          from: {
70|            height: 'var(--radix-accordion-content-height)'
71|          },
72|          to: {
73|            height: '0'
74|          }
75|        }
76|      },
77|      animation: {
78|        'accordion-down': 'accordion-down 0.2s ease-out',
79|        'accordion-up': 'accordion-up 0.2s ease-out'
80|      }
81|    }
82|  },
83|  plugins: [require("tailwindcss-animate")],
84|};
[End of file]
