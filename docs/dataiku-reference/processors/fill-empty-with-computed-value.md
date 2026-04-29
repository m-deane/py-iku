---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/fill-empty-with-computed-value.html
fetched_at: 2026-04-29
category: processors
---

# Impute with computed value

This processor imputes missing values with mean, median or mode.

The mean is the sum of values of a data set divided by number of values. This is what is most often meant by an average.

The median is the middle value separating the greater and lesser halves of a set of values

The mode is the most frequent value in a set of values

For example, given the values `1, 2, 2, 3, 4, 7, 9`:

- Mean is `4` ((1+2+2+3+4+7+9) / 7)
- Median is `3` (1, 2, 2 - **3** - 4, 7, 9)
- Mode is `2` (1, **2**, **2**, 3, 4, 7, 9)
