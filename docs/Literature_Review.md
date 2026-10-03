# Literature Review & Theoretical Foundation

This document compiles foundational peer-reviewed literature in Network Intrusion Detection Systems (NIDS) and Explainable Artificial Intelligence (XAI) supporting the research and implementation of this project.

---

### 1. Explainable AI & Feature Attribution
* **Citation:** Lundberg, S. M., & Lee, S. I. (2017). *A unified approach to interpreting model predictions.* Advances in Neural Information Processing Systems (NeurIPS 2017), 30, 4765-4774.
* **Significance:** Proposes SHAP (SHapley Additive exPlanations), demonstrating game-theoretic Shapley value optimization for additive feature attribution. Directly forms the core of our TreeSHAP local explainer.
* **Key Finding:** TreeSHAP computes exact Shapley values in polynomial time $O(TLD^2)$, making real-time flow explanation feasible during live packet inspection.

### 2. Scalable Tree Boosting (XGBoost)
* **Citation:** Chen, T., & Guestrin, C. (2016). *XGBoost: A scalable tree boosting system.* Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD 2016), 785-794.
* **Significance:** Introduces XGBoost, proposing a novel sparsity-aware algorithm and weighted quantile sketch for approximate tree learning. Delivers state-of-the-art multi-class classification accuracy on tabular network flow vectors with sub-millisecond inference time.
* **Relevance to XAI:** XGBoost's exact tree structure serves as the core base learner for TreeSHAP, enabling polynomial-time computation of game-theoretic Shapley values without Monte Carlo sampling approximations.

### 3. Benchmark Dataset & Network Traffic Characterization
* **Citation:** Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2018). *Toward generating a new intrusion detection dataset and intrusion traffic characterization.* Proceedings of the 4th International Conference on Information Systems Security and Privacy (ICISSP 2018), 108-116.
* **Significance:** Introduces the Canadian Institute for Cybersecurity (CIC) CIC-IDS2017 dataset, establishing modern multi-class attack profiles (DoS, PortScan, Brute Force, Infiltration, Botnet) based on 80+ bi-directional network flow features generated via CICFlowMeter.

### 4. Legacy Anomaly Detection Benchmarks
* **Citation:** Tavallaee, M., Bagheri, E., Lu, W., & Ghorbani, A. A. (2009). *A detailed analysis of the KDD CUP 99 data set.* IEEE Symposium on Computational Intelligence for Security and Defense Applications (CISDA 2009), 1-6.
* **Significance:** Introduces the NSL-KDD benchmark to resolve redundant records and synthetic bias present in KDD Cup 99, providing a clean comparative baseline for our academic evaluation.

### 5. Taxonomy of Network Anomaly Detection
* **Citation:** Garcia-Teodoro, P., Diaz-Verdejo, J., Maciá-Fernández, G., & Vázquez, E. (2009). *Anomaly-based network intrusion detection: Techniques, systems and challenges.* Computers & Security, 28(1-2), 18-28.
* **Significance:** Establishes the formal boundary between signature-based and anomaly-based intrusion detection, identifying the critical challenge of high false alarm rates in statistical and machine learning classifiers.

### 6. Survey on Machine Learning in Network Anomaly Detection
* **Citation:** Ahmed, M., Mahmood, A. N., & Hu, J. (2016). *A survey of network anomaly detection techniques.* Journal of Network and Computer Applications, 60, 19-31.
* **Significance:** Categorizes clustering, classification, and statistical approaches in network anomaly detection, emphasizing the imperative of bi-directional flow feature extraction over isolated raw packet inspection.

### 7. Contemporary Challenges in Cyber Defense
* **Citation:** Apruzzese, G., Laskov, P., Montes de Oca, E., Mallouli, W., Rapa, L. B., Grammatopoulos, A. V., & Di Mauro, F. (2023). *The role of machine learning in cybersecurity.* Digital Threats: Research and Practice, 4(1), 1-38.
* **Significance:** Evaluates real-world adoption of ML in commercial Security Operations Centers (SOCs), concluding that "lack of interpretability and explainability" is the number one hurdle preventing cybersecurity practitioners from acting upon algorithmic alerts.

### 8. Local Interpretable Model-agnostic Explanations (LIME)
* **Citation:** Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). *"Why should I trust you?": Explaining the predictions of any classifier.* Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 1135-1144.
* **Significance:** Foundational work in local explainability via surrogate perturbation models, providing the conceptual benchmark against which TreeSHAP's consistency and determinism are evaluated.
