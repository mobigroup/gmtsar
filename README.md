[![View on GitHub](https://img.shields.io/badge/GitHub-View%20on%20GitHub-blue)](https://github.com/AlexeyPechnikov/pygmtsar)
[![Available on pypi](https://img.shields.io/pypi/v/pygmtsar.svg)](https://pypi.python.org/pypi/pygmtsar/)
[![Docker](https://badgen.net/badge/icon/docker?icon=docker&label)](https://hub.docker.com/r/pechnikov/pygmtsar)
[![DOI](https://zenodo.org/badge/398018212.svg)](https://zenodo.org/badge/latestdoi/398018212)
[![Support on Patreon](https://img.shields.io/badge/Patreon-Support-orange.svg)](https://www.patreon.com/pechnikov)
[![ChatGPT Assistant](https://img.shields.io/badge/ChatGPT-Assistant-green?logo=openai)](https://insar.dev/ai)

## PyGMTSAR (Python InSAR): Powerful, Accessible Satellite Interferometry

<img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/c157c3a6-ed06-4b6d-82ae-c0aefb286d47" width="15%" />

PyGMTSAR (Python InSAR) is designed for both occasional users and experts working with Sentinel-1 satellite interferometry. It supports a wide range of features, including SBAS, PSI, PSI-SBAS, and more. In addition to the examples below, you’ll find more Jupyter notebook use cases on [Patreon](https://www.patreon.com/pechnikov) and updates on [LinkedIn](https://www.linkedin.com/in/alexey-pechnikov/).

## About PyGMTSAR

PyGMTSAR offers reproducible, high-performance Sentinel-1 interferometry accessible to everyone—whether you prefer Google Colab, cloud servers, or local processing. It automatically retrieves Sentinel-1 SLC scenes and bursts, DEMs, and orbits; computes interferograms and correlations; performs time-series analysis; and provides 3D visualization. This single library enables you to build a fully integrated InSAR project with minimal hassle. Whether you need a single interferogram or a multi-year analysis involving thousands of datasets, PyGMTSAR can handle the task efficiently, even on standard commodity hardware.

## PyGMTSAR Live Examples on Google Colab

Google Colab is a free service that lets you run interactive notebooks directly in your browser—no powerful computer, extensive disk space, or special installations needed. You can even do InSAR processing from a smartphone. These notebooks automate every step: installing PyGMTSAR library and its dependencies on a Colab host (Ubuntu 22, Python 3.10), downloading Sentinel-1 SLCs, orbit files, SRTM DEM data (automatically converted to ellipsoidal heights via EGM96), land mask data, and then performing complete interferometry with final mapping. You can also modify scene  or bursts names to analyze your own area of interest, and each notebook includes instant interactive 3D maps.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1TARVTB7z8goZyEVDRWyTAKJpyuqZxzW2?usp=sharing) **CENTRAL Türkiye Mw 7.8 & 7.5 Earthquakes Co-Seismic Interferogram (2023).** The area is large, covering two consecutive Sentinel-1 scenes or a total of 56 bursts.

<img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/cce39fa5-0115-467e-836d-8361a37da935" width="40%"><img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/47543745-e7b1-41cb-b9f3-6f73cb1f9fb3" width="40%">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1dDFG8BoF4WfB6tOF5sAi5mjdBKRbhxHo?usp=sharing) **Pico do Fogo Volcano Eruption, Fogo Island, Cape Verde (2014).** The interferogram for this event is compared to the study *The 2014–2015 eruption of Fogo volcano: Geodetic modeling of Sentinel-1 TOPS interferometry* (*Geophysical Research Letters*, DOI: [10.1002/2015GL066003](https://doi.org/10.1002/2015GL066003)).

<img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/d2eda089-0730-4699-82db-9410712d55ff" width="40%"><img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/694d9670-36c9-4e56-bfb8-056e0d038d58" width="40%">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1d9RcqBmWIKQDEwJYo8Dh6M4tMjJtvseC?usp=sharing) **La Cumbre Volcano Eruption Interferogram (2020).** The results compare with the report from Instituto Geofísico, Escuela Politécnica Nacional (IG-EPN) (InSAR software unspecified).

<img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/93cc9c5c-a654-4cc6-a310-2f3337c95ce2" width="40%"><img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/fe085c2b-5bd5-4385-a1fe-04144568e1cb" width="40%">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1shNGvUlUiXeyV7IcTmDbWaEM6XrB0014?usp=sharing) **Iran–Iraq Earthquake Co-Seismic Interferogram (2017).** The event has been well investigated, and the results compared to outputs from GMTSAR, SNAP, and GAMMA software.

<img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/7357a56a-d69f-451b-91ab-367cbf2af410" width="40%"><img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/bcd807f9-5d48-4bb4-ac13-803305f3b6da" width="40%">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1h4XxJZwFfm7EC8NUzl34cCkOVUG2uJr4?usp=sharing) **Imperial Valley SBAS Analysis (2015).**  This example is provided in the [GMTSAR project](https://topex.ucsd.edu/gmtsar/downloads/) in the archive file [S1A_Stack_CPGF_T173.tar.gz](http://topex.ucsd.edu/gmtsar/tar/S1A_Stack_CPGF_T173.tar.gz), titled 'Sentinel-1 TOPS Time Series'.

The resulting InSAR velocity map is available as a self-contained web page at: [Imperial_Valley_2015.html](https://insar.dev/ui/Imperial_Valley_2015.html)

<img src="https://github.com/user-attachments/assets/66f936af-ce21-485d-b11d-f3539aa82cdc" width="40%"> <img src="https://github.com/user-attachments/assets/d2f55e44-dc26-4a0f-bebe-cd0f4950b4f3" width="40%">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1aqAr9KWKzGx9XpVie1M000C3vUxzNDxu?usp=sharing) **Flooding [Correlation] Map: Kalkarindji, NT Australia (2024).** Correlation loss serves to identify flooded areas.

<img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/368e5fc2-1966-4f98-a03d-e82b50103c05" width="80%">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1ipiQGbvUF8duzjZER8v-_R48DSpSmgvQ?usp=sharing) **PyGMTSAR SBAS & PSI: Golden Valley, CA.** This example demonstrates the case study 'Antelope Valley Freeway in Santa Clarita, CA,' as detailed in [SAR Technical Series Part 4 | Sentinel-1 global velocity layer: Using global InSAR at scale](https://blog.descarteslabs.com/using-global-insar-at-scale) and [Sentinel-1 Technical Series Part 5 | Targeted Analysis](https://blog.descarteslabs.com/sentinel-1-targeted-analysis) with a significant subsidence rate 'exceeding 5cm/year in places'.

<img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/8b416787-4b81-44f8-8956-3a5d596af51b" width="80%">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1O3aZtZsTrQIldvCqlVRel13wJRLhmTJt?usp=sharing) **PyGMTSAR SBAS & PSI: Lake Sarez Landslides, Tajikistan.** The example reproduces the findings shared in the following paper: [Integration of satellite SAR and optical acquisitions for the characterization of the Lake Sarez landslides in Tajikistan](https://www.google.com/url?q=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F378176884_Integration_of_satellite_SAR_and_optical_acquisitions_for_the_characterization_of_the_Lake_Sarez_landslides_in_Tajikistan).

<img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/b507cad0-db7a-47e6-a679-f74631c5e840" width="80%">

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/19PLuebOZ4gaYX5ym1H7SwUbJKfl23qPr?usp=sharing) **PyGMTSAR Elevation Map: Erzincan, Türkiye.** This example reproduces 29-page ESA document [DEM generation with Sentinel-1 IW](https://step.esa.int/docs/tutorials/S1TBX%20DEM%20generation%20with%20Sentinel-1%20IW%20Tutorial.pdf).

<img src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/066532d5-7b07-49d2-9478-7b8f966a3752" width="80%">

## More PyGMTSAR Live Examples on Google Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1yuuA1ES2ly4QG3hyPg8YYT0nnpGDiQDw?usp=sharing) **Mexico City Interferogram (2016).** This example replicates the 29-page ESA manual [TRAINING KIT – HAZA03. LAND SUBSIDENCE WITH SENTINEL-1 using SNAP](https://eo4society.esa.int/wp-content/uploads/2022/01/HAZA03_Land-Subsidence_Mexico-city.pdf).

## PyGMTSAR Live Examples on Google Colab Pro

I share additional InSAR projects on Google Colab Pro through my [Patreon page](https://www.patreon.com/pechnikov). These are ideal for InSAR learners, researchers, and industry professionals tackling challenging projects with large areas, big stacks of interferograms, low-coherence regions, or significant atmospheric delays. You can run these privately shared notebooks online with Colab Pro or locally/on remote servers.

## Projects and Publications Using PyGMTSAR

See the [Projects and Publications](/pubs/README.md) page for real-world projects and academic research applying PyGMTSAR. This is not an exhaustive list—contact me if you’d like your project or publication included.

## Resources

**PyGMTSAR projects and e-books**  
Available on [Patreon](https://www.patreon.com/c/pechnikov/shop). Preview versions can be found in this GitHub repo:

- [PyGMTSAR Introduction Preview](https://github.com/AlexeyPechnikov/pygmtsar/blob/pygmtsar2/book/PyGMTSAR_preview.pdf)  
- [PyGMTSAR Gaussian Filtering Preview](https://github.com/AlexeyPechnikov/pygmtsar/blob/pygmtsar2/book/Gaussian_preview.pdf)

<img src="https://github.com/user-attachments/assets/757b1b4d-7429-4977-8d43-afdf7e1185bd" width="40%">

**Video Lessons and Notebooks**  
Find PyGMTSAR (Python InSAR) video lessons and educational notebooks on [Patreon](https://www.patreon.com/collection/12458) and [YouTube](https://www.youtube.com/channel/UCSEeXKAn9f_bDiTjT6l87Lg).

**PyGMTSAR AI Assistant**  
The [PyGMTSAR AI Assistant](https://insar.dev/ai), powered by OpenAI ChatGPT, can explain InSAR theory, guide you through examples, help build an InSAR processing pipeline, and troubleshoot.

<img width="40%" alt="PyGMTSAR AI Assistant" src="https://github.com/AlexeyPechnikov/pygmtsar/assets/7342379/f1b7780d-9a93-4277-b9c3-9e54d9ff3d8b">

**PyGMTSAR on DockerHub**  
Run InSAR processing on macOS, Linux, or Windows via [Docker images](https://hub.docker.com/r/pechnikov/pygmtsar).

**PyGMTSAR on PyPI**  
Install the library from [PyPI](https://pypi.python.org/pypi/pygmtsar).

**PyGMTSAR Previous Versions**  
2023 releases are still on GitHub, PyPI, DockerHub, and Google Colab. Compare PyGMTSAR InSAR with other software by checking out the [PyGMTSAR 2023 Repository](https://github.com/AlexeyPechnikov/pygmtsar/tree/pygmtsar).

© Alexey Pechnikov, 2025