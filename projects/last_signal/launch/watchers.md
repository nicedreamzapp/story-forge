# Watchers — replies, negative feedback, one-step takedown (DESIGN DRAFT, nothing built)

Matt (via coordinator): watch closely for negative feedback and be ready to take posts down. Heavy watching lives on the **mini**, never the M5. Code first: a model wakes only when a new comment exists. Alerts are texts from the mini. Takedown should be one step once he says so.

## What exists today (checked live on the mini, 10/31)

| Platform | Watcher now | Frequency | What it does | Gap for this launch |
|---|---|---|---|---|
| Reddit | `reddit-inbox` (`com.divinetribe.reddit-inbox`) | every 30 min (StartInterval 1800) | Reads u/divinetribe1's inbox through the API and emails Matt (not a text). It holds anything outside 7am to 7pm, drops short "pleasantries" and anything older than 2 weeks, and **never** looks at score, upvote ratio or mod removal | A short "ai slop" can be dropped as too short. Removal and downvotes are invisible. It emails instead of texting. It logged 4 API errors (500/404) in the last 3 days |
| YouTube | **none scheduled**. `~/Scripts/yt-comments/yt_comments.py` exists on the **M5** only (read only, manual, prints every comment) | n/a | n/a | Nothing watches YouTube. The OAuth token and `yt_auth.py` are on the M5 only; the mini has no copy |
| X | `x_reply_mail.py` (`com.divinetribe.x-reply-mail`) | every 15 min | HQ Gmail search for X notification emails, texts Matt one line per new one. Plain code | No sentiment and no delete tool. Matt chose email over the browser walk on 10/31 1:46 AM, so keep it email based |
| LinkedIn | `linkedin-comment-watch` (`com.nicedreamz.linkedin-comment-watch`) | 7 runs a day, 9:20 AM to 9:20 PM, every 2 h | Hidden broker tabs walk his recent posts and text him per new unanswered comment. It picks up new posts on its own | Too slow for a launch's first hours, no sentiment, no delete tool |
| GitHub | `gh-watcher` (`com.nicedreamz.ghwatcher`) | every 15 min | Texts on issues and PRs on his repos | Fine as is. The repo isn't a takedown target (use `git revert` if ever needed) |
| Website | none needed | n/a | A static page we control | Takedown = restore the backup file |

Text channel on the mini: `~/.claude/imessage-send.sh "msg"` (present). There's **no always-on local LLM endpoint on the mini**: I probed 8000, 8001, 8790-8797, 8900, 9000 and 176xx for `/v1/models` and none answered. So the model step has to load on demand.

## The design: `launch-watch` on the mini

**Where:** `~/scripts/launch-watch/` on the mini, LaunchAgent `com.nicedreamz.launch-watch`, StartInterval **600 s** (a 10 min tick), run through `hb-run` and registered in agent-watchdog like the others. Plain Python, no browser for Reddit or YouTube.

**Targets:** `targets.json`, one entry per live post, added by whoever posts it, the moment it goes up:
`launch-watch --add reddit t3_abc123 "r/StableDiffusion"` · `--add youtube VIDEOID` · `--add x 1234567890 --thread 3` · `--add linkedin urn:li:activity:NNN`

**Cadence per target (cheap API calls, so it can run tight):** every 10 min for the first 6 h, every 30 min until 48 h, every 2 h until day 7, then retire the target and log it.

**Per platform, code first:**
- **Reddit (API, creds already on the mini at `~/.config/secrets/reddit.env`):** `GET /api/info?id=t3_X` for score, upvote_ratio, num_comments, removed_by_category, locked. `GET /comments/X?sort=new&limit=500` for new comment IDs. **Red flags with no model needed:** `removed_by_category` set (text at once, any hour), a comment `distinguished: moderator`, upvote_ratio under 0.60 with 10 or more votes after 30 min, score at 0 or below after 60 min.
- **YouTube (Data API, the token copied to the mini at `~/.config/secrets/youtube/token_nicedreamz.json`, never a cloud folder):** `videos.list part=statistics,status` (views, likes, commentCount, privacyStatus, uploadStatus, rejectionReason) and `commentThreads.list order=time`. Quota is about 300 units a day at peak cadence, against the 10,000 daily limit. Dislikes aren't in the Data API. They'd need the YouTube Analytics API (`yt-analytics.readonly` scope), which the current token doesn't have, so it's a one-time re-consent if Matt wants dislike counts.
- **X (email, no browser):** extend `x_reply_mail.py` so any email whose link points at a registered launch tweet hands its reply text to launch-watch's sentiment step instead of the plain one-liner.
- **LinkedIn (email first):** LinkedIn emails "commented on your post" notifications. An HQ Gmail search (`from:linkedin.com newer_than:2d "commented on"`) gives the text with no browser. Keep the existing 2 h browser walk as the backstop.

**Sentiment, code first, then a model only on new text:**
1. A new comment arrives (a new ID we haven't seen). If there's nothing new, no model call, ever.
2. A plain regex score on the text: slop, ai slop, garbage, trash, fake, lie/lying, misleading, clickbait, not local, cloud, stolen, theft, copyright, ripoff, lazy, soulless, uncanny, cringe, spam, shill, ad, bot, reported, mods, removed, plus all caps and expletive weight. Positive words lower the score.
3. Only for new comments, load a local model on demand (with a memory lease via `mem_client.reserve`, unloaded after the batch, never resident) and get back `{sentiment: positive|neutral|negative|hostile, is_mod_or_rules: bool, factual_challenge: bool, needs_reply: bool, takedown_signal: 0-3}`. Per Matt's model rule this must be a **vision-capable model already on the mini**. I didn't verify which one is on disk there, so that's open.
4. A `factual_challenge` (someone saying "this isn't local" or "that's not 4K") gets flagged even when the tone is polite, because those are the ones to answer fast and honestly. The real caveats (the upscaled 4K, the CC-NC voice) are already written down in known_defects.md for the reply.

**Alerts (texts from the mini):**
- **Right away, any hour:** a mod removal, a mod comment, `takedown_signal` 3, ratio or score red flags, a YouTube rejection or status change.
- **Batched hourly, 7 AM to 10 PM:** everything else, one line per post: `[LAST SIGNAL r/StableDiffusion] +6 comments, 1 negative ("...first 80 chars..."), ratio 0.91, score 48. Takedown: reply TD SD`.
- Every alert ends with the takedown tag for that post: TD SD, TD LTX, TD AIV, TD YT, TD X, TD LI.

**One-step takedown:** Matt texts back `TD <tag>`, or says it in any chat. The watcher reads his reply the same way promo-watch reads his yes for `[SUB]` drafts (state.json approvals), runs the matching command below, verifies it, and texts back "taken down, verified". His reply **is** the authorization. Nothing is ever taken down on a score alone.

## Takedown commands per platform

| Tag | Platform | Command / path | Reversible? | Exists today? |
|---|---|---|---|---|
| TD SD / TD LTX / TD AIV | Reddit | `takedown.py reddit t3_X`: OAuth password grant from `~/.config/secrets/reddit.env`, then `POST https://oauth.reddit.com/api/del` with `id=t3_X`, then the same for our first comment `t1_Y`. Verify that `/api/info` shows `[deleted]` | No (Reddit has no unlist) | **Needs building.** `inbox.py`'s client is read only by design; write a separate 30 line script on the mini |
| TD YT (soft) | YouTube | `videos().update(part="status", body={"id": VID, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "embeddable": True}})`. Verify with `videos.list` | **Yes**, flip back to public any time | Token scope `youtube` already allows it (verified live 10/31). The script needs writing; until the token lives on the mini, run it on the M5 from `ineedhemp website/youtube/` with `.venv/bin/python` |
| TD YT (hard) | YouTube | `videos().delete(id=VID)` | No | Same token. Only if Matt says "delete", not "take down" |
| TD X | X | `x_delete.py <status_url> [--thread]` on the mini: one hidden broker tab, open the status, click aria "More", menuitem "Delete", confirm "Delete", check the URL now shows "This post was deleted" or 404, **bb-close the tab**. For a thread, delete the parts in reverse order | No | **Needs building.** `x_feed_actions.py` has follow, read, search and hide, no delete. There's no X API key in use |
| TD LI | LinkedIn | `linkedin_delete.py urn:li:activity:NNN` on the mini: hidden broker tab, open `linkedin.com/feed/update/<urn>/`, "Open control menu", "Delete post", confirm, verify gone, **bb-close** | No (an "edit" is the soft option) | **Needs building.** `~/Scripts/linkedin_post.py` (M5) only posts |
| (page) | Story Forge page | `ssh ineedhemp 'cd domains/nicedreamzwholesale.com/public_html/software/story-forge && cp index.html.bak-lastsignal-20261031 index.html && cd ../.. && wp cache flush'` | Yes | Works as soon as the deploy makes that backup |
| (repo) | GitHub | `git revert <sha> && git push` (never a force push, never a history rewrite) | Yes | Works today |

## Build estimate (not started, needs Matt's go)
About 2 h on the mini, Opus (it's judgment and destructive actions). launch-watch core plus Reddit and YouTube is about 60 min. The X and LinkedIn delete scripts are about 30 min each, tested only on a throwaway post Matt OKs first, never on the launch posts. Copying the YouTube token to the mini (`~/.config/secrets/youtube/`, chmod 600) is 5 min. Then add it to agent-watchdog and the HQ catalog. It should be live **before** the first post goes up, so the first hours are covered.
