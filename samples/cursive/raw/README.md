# NCCU cursive subset

This directory contains a small, redistributable subset downloaded from [nccuviplab/CursiveChineseCalligraphyDataset](https://github.com/nccuviplab/CursiveChineseCalligraphyDataset).

The dataset is licensed under the MIT License. The source README states that its administrator reorganized and redistributed calligraphy images with permission from the administrator of https://shufa.supfree.net/.

The subset exists to make the local demo and batch-typesetting workflow executable. It is not a complete copy of the 1.4 GB upstream repository.

To refresh or expand it:

```powershell
python scripts/fetch_nccu_subset.py --characters "春眠不觉晓处闻啼鸟" --variants 2 --output samples/cursive/raw
```

`metadata.json` records every downloaded source path. See `LICENSE` for the full MIT grant.
