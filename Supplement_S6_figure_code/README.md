# Figure code

`draw_figures.py` draws the schematic figures of the article deterministically with matplotlib: Fig. 1 (question-specific comparisons, five rows since version 1.1.0) and Fig. 3 (typed repair and independent verification); the script also draws an earlier figure no longer used in the article. The figures contain no measured quantities. Fig. 2, the only data figure, is drawn by `Supplement_S8_outlier_redistribution_audit/code/make_outputs.py`.

```
python3 draw_figures.py OUTPUT_DIR
```
