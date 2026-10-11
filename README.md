# Everstack Studio pin feeds

Public on purpose: this repo holds only pins Jason approved (image, title, description, link) and the
feed builder. No secrets, no tokens.

## How it works

1. Pins are drafted and approved in the private repo `jtrathjen/everstack-social` and exported here
   with `toolkit/pins.py export`. `pins.json` lists every approved pin with its board and
   `publish_after` date.
2. The **Build pin feeds** workflow runs on every push and daily at about 8:17 AM Chicago time. It
   builds one RSS feed per board from the pins whose date has arrived and deploys it to GitHub Pages.
3. Pinterest auto-publish reads each feed and turns every new item into a Pin on that feed's board,
   usually within 24 hours.

## Feeds

| Board | Feed URL |
| --- | --- |
| Holiday Budget & Gift Planning | https://jtrathjen.github.io/everstack-pins/holiday.xml |
| Performance Review Templates | https://jtrathjen.github.io/everstack-pins/work.xml |

Connect each feed once, on a computer: Pinterest > Settings > Create Pins in bulk > Auto-publish >
Connect RSS feed > paste the feed URL > choose its board > Save.

## Good to know

- To stop a pin that hasn't gone out yet, withdraw it in `everstack-social` and export again. A Pin
  Pinterest already made stays up until it's deleted on Pinterest.
- GitHub pauses scheduled workflows in a public repo after 60 days without commits. If that happens,
  turn it back on under Actions > Build pin feeds > Enable workflow.
