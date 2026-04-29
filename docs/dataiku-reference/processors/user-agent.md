---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/user-agent.html
fetched_at: 2026-04-29
category: processors
---

# Classify User-Agent

This processor parses and extracts information from a browser's User-Agent string.

The following columns are created and may or may not be filled depending on the user agents:

- **type**: one of:
  - 'browser' (desktop OS)
  - 'tablet'
  - 'phone'
  - 'mobile' (could be either a tablet or phone)
  - 'bot' (crawlers, spam, ...)
  - 'library' (wget, urllib2, ...)
  - 'rss': RSS feed readers
  - 'unknown'

- **brand**: Chrome, Firefox, Safari, Android, ...

- **category**: Quite like brand, but tries to distinguish browsers of the same brand that behave differently. For example, IE8 and IE9 are the same brand, but different categories

- **version**

- **os**: Operating system

- **osversion**: Version of the Operating system

- **osflavor**: Variant of the Operating System (Linux distribution, 32/64 bits, ...)
