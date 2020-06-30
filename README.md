# MMS SITL Ground Loop: Automating the burst data selection process

Global-scale energy flow throughout Earth’s magnetosphere is catalyzed by processes that occur at Earth’s magnetopause (MP) in the electron diffusion region (EDR) of magnetic reconnection. Magnetic reconnection is an explosive process by which magnetic field lines from the Earth and Sun break and reconnection, releasing vast amounts of energy. To study the electron dynamics that trigger reconnection, large volumes of high time resolution data are required -- more data than can be downlinked to Earth. To ensure the right data is returned, NASA science missions typically employ burst triggers, a type of look-up table of threshold values applied to data from each instrument. The Magnetospheric Multiscale (MMS) mission also uses a human Scientist-in-the-Loop (SITL) who searches through low time resolution data to identify (among other things) the magnetopause, the boundary between the Earth and Sun's magnetic field where reconnection is likely to occur.

We use machine learning to classify magnetopause crossings, thereby automating a critical SITL task. To do so, we used historical SITL classifications and data available to the SITL at the time they make their selections. Features are derived from the Analog Fluxgate Magnetometer, Electric Field Double Probes, and Fast Plasma Investigation instruments on MMS. We find that the initial model is able to correctly identify 75% of all burst selections classified as magnetopause crossings by the SITL, and 70% of all model selections are also selected by the SITL.

The code we used for this study is included in this repository as an ipython notebook (to view the ipython notebook, use the [Jupyter notebook viewer](http://nbviewer.jupyter.org/)). It uses libraries from [TensorFlow](https://www.tensorflow.org/) for the machine learning analysis. The ipython notebook and additional data files are also permanently available in the **Zenodo Digital Repository**. To read more about the research, see **Argall, Small, et al. (2020**.

If you reference GLS-MP in your academic projects in the context of its deployment at the SDC, please cite **Argall, Small, et al. (2020)**. To cite the library in general, you could use this BibTeX entry:

```
@misc{gls-mp,
title = {{GLS-MP}: automated magnetopause crossing detection,
author = {Small, C.R., Argall, M.R., Petrik, M.},
note = {https://github.com/colinrsmall/GLS-MP},
year = {2020},
doi = {10.5281/zenodo.3891992},
}
