---
title: "There is no best web scraper — and picking one is the mistake"
type: essay
date: 2026-05-18
status: draft
---

# There is no best web scraper — and picking one is the mistake

Every time I asked an agent to fetch a web page, one of two things happened. It
failed — a bot wall, an empty render, a 200 response with no content — or it worked
but cost far more than it should have. A single Wikipedia article would land 86,000
tokens of HTML noise in my context. A pricing page I needed four numbers from would
arrive as a 2,400-token wall.

The reflex is to go find the *best* scraping tool and standardize on it. I did that
a few times. It never held. The tool that's brilliant on a static article is the
wrong tool for a React SPA. The one that's fast on an SPA returns 1.8k useless
tokens on a GitHub repo. The one that handles social media is an API you pay for,
so you don't want it touching a page a free local tool could have read.

There is no best scraper. There's a best scraper *for this page*, and which page
it is changes every single call. So the thing worth building isn't a scraper. It's
the decision.

## The two costs nobody measures

When people compare scraping tools they compare whether it works. That's one cost.
The one that quietly hurts more is tokens.

Here's the same content through four tools, measured:

| Tool | Wikipedia article | Pricing page |
|---|---|---|
| trafilatura | 24k tokens | 418 tokens |
| webclaw | — | 980 tokens |
| playwright | 47k tokens | 2,400 tokens |
| jina | 86k tokens | — |

These all "work." They all return the content. But trafilatura uses **3–5× fewer
tokens** than the alternatives on server-rendered pages — and on the pricing page,
418 tokens versus 2,400 is the difference between a fetch you barely notice and one
that eats a measurable slice of your context window.

Multiply that across a research session with thirty fetches and the wrong default
isn't a rounding error. It's the reason the agent runs out of room to think halfway
through. The token cost of a scrape is invisible until you measure it, and once you
measure it you can't un-see it.

## What I actually wanted

I didn't want a better scraper. I wanted to stop thinking about scraping.

Specifically, I wanted something that could:

- **Understand my intent and route on its own.** I say "fetch this." It looks at
  what *this* is — an article, a SPA, a PDF, a YouTube link, a paywalled story —
  and picks the tool. I don't want to know that GitHub repos need a different tool
  than Notion pages. I want that knowledge to live in the system, not in my head.
- **Stay out of my main session.** Scraping is messy work — retries, escalations,
  raw HTML. None of that belongs in the conversation where I'm actually trying to
  get something done. It should happen off to the side and hand back only the clean
  result.
- **Remember what it did.** Store the retrieved content to disk instead of dumping
  it raw into context. Log every fetch — which URL, which tool, did it succeed,
  did it come back suspiciously thin. So when something fails I can see *why*, and
  the system can learn from its own failures instead of repeating them.

That's not one tool. That's a suite with a router on the front, a memory behind it,
and a log underneath. So that's what I built.

## Local first, and free

One rule sits above all the routing: **local free tools run first; paid APIs are a
last resort.**

This isn't only about money, though the money is real — API scraping credits add up
fast and silently. It's about not reaching for a credit-metered service to do a job
a free local tool does better anyway. trafilatura runs on your machine, costs
nothing, and beats the paid options on token efficiency for static content. Why
would you pay an API to do that worse?

So the escalation chains all start local — trafilatura, webclaw, playwright, a local
search instance — and only fall through to free-tier APIs, and finally to credits,
when local genuinely can't get there. Most pages never leave the free local tier.
The system is free by default, and stays free unless a page forces the issue. When
it does have to spend a credit, it tells you, instead of failing silently or
quietly draining a balance.

The point of "free" isn't frugality for its own sake. It's that a tool you have to
budget for is a tool you think about. A tool that's free by default is one you can
forget — which was the whole goal.

## Simple to set up, simple to make yours

A router is only useful if it's not a project to adopt. One health check verifies
the tools, tells you exactly what's missing and the command to fix it, and caches
the result so it never nags you again. The routing rules are plain text — you can
read them, fork them, add a tool, change a default, point a content type somewhere
else, even escalate the session to a custom flow when a project needs more
efficiency than the general case gives. It's a suite you can personalize, not a
black box you have to trust.

I wanted it to be the kind of thing you set up once and then never open again.

## The claim

It's narrow. When a task has no single right tool — and web scraping doesn't — the
valuable artifact is not the best tool. It's the system that picks.

Standardizing on one scraper feels like a decision. It's actually deferring the
decision to every future page, and being wrong on most of them — wrong on
correctness when the page doesn't suit the tool, wrong on cost when a cheaper tool
would have done it for a fifth of the tokens. Routing moves that decision into the
system, once, where it can be measured, logged, and improved.

The honest result: I don't think about how to fetch a web page anymore. I say
"fetch this," and it works — every time, for free, off to the side, without my
attention. That's the entire point.

I built [`scrapekit`](https://github.com/alexsmedile/scrapekit) so I could stop
thinking about scraping. The router is just the convenient form of the argument —
the argument stands on its own.

```bash
/plugin marketplace add alexsmedile/scrapekit
```
