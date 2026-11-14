---
title: "More Efficient Data Gathering for World Models"
subtitle: "Not all observations are created equal"
date: 2026-10-13
source: deleon
original_url: "https://deleon.bio/article?slug=information-space"
summary: "Exploreon chooses the next experiment for each person in a study. In simulation it reached the same final accuracy as Claude Opus 5.5 and Monte Carlo sampling with 7x and 12x less data."
---

![Model accuracy against experimental data collection cost](https://deleon.bio/articles/information-space/accuracy-vs-cost.jpg)
*Figure 1. Model accuracy against experimental data collection cost, counting every data point as equally costly to collect (Opus 5.5 tokens are not included). Exploreon reaches the same final accuracy as a frontier LLM or Monte Carlo sampling with 7x and 12x less data, respectively.*

If you have a high cost per data point, the highest-leverage thing you can do is figure out which data points will be most important to your world model's performance.

Companies have been pouring tens of billions of dollars into creating unique datasets specifically suited for world models of various types: from robotics firms putting cameras on people's heads, to in vitro biology companies building automated labs to run assays on cells.

The problem is that these rigs are expensive, and these data are hard to collect compared to text. This may not have mattered much when training early LLMs, when teams could scrape the Internet and brute-force their way to intelligence with any text they could find. But when your AI is meant to interact with the real world, you hit physical limits fast.

On top of that, training these models takes a long time. By the time you've benchmarked your new model and you know what it's deficient at, you've got to start another run with the dataset that you have been blindly collecting. Decisions about what data to invest in next don't get baked in until the next model.

So, what if you could know exactly what data points you are missing in your dataset? That's what we built with Exploreon.

## Exploring biological space efficiently

Deleon's Otea changes how we study metabolism. Our at-home, lab-grade device can run cross-sectional and personalized metabolism studies every day at an unprecedentedly low cost. Paired with our biobanking campaign, it is powering our first large program, which will examine how nutrition, training, and sleep shape the metabolites present in urine. Still, building that dataset means solving a new problem: deciding which experiments are worth running.

So along the way we built Exploreon, a tool that answers that question. It guides the construction of our dataset to speed up training of our first world model for human metabolism. As a platform, it helps Deleon choose the next experiment for each person being studied, based on what we already learned about them, and about the rest of the population.

But the problem it solves is not specific to us. Any study of the physical world with many possible inputs faces the same challenge. This is where Exploreon's real value becomes apparent: it is a generalized tool for triaging real-time experiments that generate data for AI world models.

*Figure 2 (on the [original post](https://deleon.bio/article?slug=information-space)). Estimated amino acid probability density functions after 180 days of feedback-guided exploration of the experimental space, compared with Monte Carlo sampling and frontier LLM-guided estimations.*

In Figure 1 we show that the dataset constructed by Exploreon trains an LSTM to model a representative ODE to the same final accuracy[^1] as datasets chosen by a frontier LLM (Claude Opus 5.5) or by simple Monte Carlo sampling, while using 7 and 12 times less data, respectively. Figure 2 shows how each sampling approach explores the output space of the same ODE over the days of a simulated in vivo metabolism experiment, by tracking how the estimated amino acid probability density functions (the joint distribution of observed glutamine and tryptophan concentrations) fill in as samples accumulate.

Some measurements teach us new things about how the body responds to an intervention, while others only confirm what we know. Exploreon distinguishes these by modeling what we believe about how a person's inputs will affect their metabolic response, and by tracking how uncertain that belief becomes as you add more data nearby. We optimize for the experiments that reduce uncertainty most. Daily biochemical feedback to Exploreon will be enabled by Otea, thus making our sampling more efficient.

Each new measurement updates the model and changes what the next experiment should be. Time matters as well: a metabolic measurement taken the day after a hard workout tells us something different from one taken after a rest day, so the platform accounts for what came before. In our case, each person being studied has their own variations, which reasoning LLMs can identify and explain so Exploreon can account for them when choosing what to test next.

[^1]: Figure 1 shows the accuracy of an LSTM trained on the first d days of each dataset, scored on 20 held-out participants over all 180 days. Accuracy is 100% minus the normalised RMSE (NRMSE). Each amino acid's RMSE against the ODE's noise-free readings is divided by its mean reading in the held-out set (glutamine 229 µmol/L, tryptophan 25 µmol/L), and the two NRMSEs are averaged. Accuracy therefore measures how close a typical prediction is to the true reading, not the fraction of predictions that are correct.
