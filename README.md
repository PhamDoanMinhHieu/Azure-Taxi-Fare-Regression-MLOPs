# Azure Taxi Fare Regression — MLOps Lab

A complete, hands-on **Azure Machine Learning MLOps pipeline** that trains a regression
model to predict NYC taxi fares, built as a practice lab for the **Azure MLOps Engineer**
role. It follows the "inner loop" architecture of
[Azure/mlops-project-classical-ml](https://github.com/Azure/mlops-project-classical-ml)
(part of [Azure/mlops-v2](https://github.com/Azure/mlops-v2)), using Azure ML CLI v2
component/pipeline specs.

The lab is documented **two ways** so you can practice either skill set:

| Track | What you use | Best for |
|---|---|---|
| **A — Azure Portal** | Point-and-click in [portal.azure.com](https://portal.azure.com) / Azure ML Studio | Learning the Studio UI, demos, first-time exploration |
| **B — CLI / Scripts** | `az` CLI + the `scripts/` wrappers (Infrastructure-as-Code) | Reproducible runs, automation, CI/CD groundwork |

Both tracks build the **exact same pipeline** from the **exact same YAML specs** in this
repo — pick one, or do Portal first to understand the pieces and then CLI to automate them.

---

## 1. Architecture

```
data/ (yellow + green taxi CSV)
        │
        ▼
  prep-job        merge yellow+green, clean, feature engineering, train/val/test split
        │
        ▼
  train-job       Linear Regression (scikit-learn), logged via MLflow autolog
        │
        ▼
  evaluate-job     compute R²/MSE on the test set, compare against the currently
        │          registered model (deploy_flag = 1 if the new model is better
        │          or none exists yet)
        ▼
  register-job     register the model into the Azure ML Model Registry if deploy_flag = 1
        │
        ▼
  (optional) Managed Online Endpoint — real-time REST scoring, data collection
             + Model Monitoring for drift/quality
```

Each step is an independent, reusable **Azure ML Component** (`components/<step>/`),
wired together in [pipeline.yml](pipeline.yml).

## 2. Repository structure

```
data/                     Sample raw data (yellow/green taxi CSV)
components/
  prep/                   Merge, clean, feature-engineer, split train/val/test
    prep.yml                component spec (inputs/outputs/environment/command)
    src/prep.py
    prep_component.zip      ready-to-upload package for Studio's "Register component" wizard
  train/                  Train a scikit-learn LinearRegression model
  evaluate/               Score on the test set, decide whether to deploy
  register/               Register the model in the Model Registry
environment/              Shared conda environment definition (training + serving)
deployment/               Managed Online Endpoint: scoring script + CLI v2 specs
infra/                    Bicep: Resource Group + Workspace + Compute Cluster (IaC)
scripts/                  CLI wrapper scripts (Track B) — run the lab end-to-end
pipeline.yml              Azure ML pipeline job definition (CLI v2)
```

## 3. Prerequisites

- An Azure subscription (a [free trial](https://azure.microsoft.com/free/) is enough).
- **Track A only:** a browser and access to [portal.azure.com](https://portal.azure.com).
- **Track B only:** [`az` CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
  installed and logged in (`az login`), plus the Azure ML extension:
  ```bash
  az extension add -n ml
  ```

---

## Track A — Azure Portal (manual, click-through)

This is the path used to originally build and validate this lab. Every step below is a
Portal UI action — no CLI required.

### A1. Provision infrastructure
1. **Resource groups** → **Create** → pick a name (e.g. `rg-taxi-mlops`) and region.
2. Inside it, **Create a resource** → **Azure Machine Learning** → create a workspace
   (e.g. `aml-taxi`). This auto-creates the Storage Account, Key Vault and
   Application Insights it depends on.
3. Open **Azure ML Studio** (`ml.azure.com`) → **Manage → Compute** → **Compute clusters**
   → **New** → name it `taxi-cpu-cluster`, pick a small CPU VM size (e.g.
   `Standard_DS3_v2`), min nodes `0`, max nodes `2` (scales to zero when idle).

   > ⚠️ Make sure you create a **Compute cluster** (autoscaling, for jobs), not a
   > **Compute instance** (a single always-on VM) — they look similar in the UI but
   > behave very differently for billing and pipeline execution.

### A2. Register the training/serving environment
1. **Assets → Environments** → **Create** → **Custom**.
2. Base image: `mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest`.
3. Paste the contents of [environment/conda.yaml](environment/conda.yaml) into the conda
   editor, then **Create**. Wait for the build status to reach **Succeeded** (3–8 min).
4. Open the **Context** tab afterwards and confirm `setuptools` and
   `azureml-inference-server-http` appear **inside** the `pip:` block — see
   [§6 Lessons learned](#6-lessons-learned--troubleshooting) for why this matters.

### A3. Upload the data asset
1. **Assets → Data** → **Create** → **Folder (uri_folder)**.
2. Upload the whole [`data/`](data) folder (both CSVs together — `prep.py` expects to
   find both files in the same input folder).
3. Name it e.g. `taxi-raw-data`.

### A4. Register the 4 pipeline components
For each of `prep`, `train`, `evaluate`, `register`:
1. **Assets → Components** → **Register component** → **From local files** →
   **Zip file**.
2. Upload `components/<step>/<step>_component.zip` (already built and committed in this
   repo — contains the component's `.yml` spec at the zip root plus its `src/` folder).
3. Studio auto-detects the YAML spec (name, inputs/outputs, environment, command) —
   review and **Create**.

### A5. Build and run the pipeline (Designer)
1. **Authoring → Designer** → **New pipeline**.
2. Drag in `taxi-raw-data` and the 4 components; wire them exactly as in
   [§1 Architecture](#1-architecture) / [pipeline.yml](pipeline.yml):
   `raw_data → transformed_data → training_data/test_data → model_output →
   model_input/model_path → deploy_flag`.
3. **Configure & Submit**: compute = `taxi-cpu-cluster`, identity type = `AMLToken`,
   uncheck "Continue on step failure".
4. Watch all 4 steps turn green. Check **Metrics** on `evaluate-model` for `mse`/`r2`,
   and **Assets → Models** for the newly registered `taxi-model`.

### A6. Deploy a Managed Online Endpoint
1. **Assets → Models** → `taxi-model` → **Deploy** → **Real-time endpoint**.
2. Name it `taxi-fare-endpoint`, auth mode = **Key**.
3. Environment: reuse the custom environment from A2 (`taxi-fare-train-env`).
4. Scoring script: upload [deployment/score.py](deployment/score.py).
5. Compute: a small VM (e.g. `Standard_DS2_v2`), instance count `1`.
6. Wait for the deployment to reach **Succeeded**, then test it from the endpoint's
   **Consume** tab (REST URL + key) or **Test** tab with the payload in
   [deployment/sample-request.json](deployment/sample-request.json).

### A7. Enable monitoring
1. On the deployment, enable **Data collection** for `model_inputs` and
   `model_outputs`.
2. **Manage → Monitoring** → **Create** → target the endpoint/deployment, pick
   **Data drift** / **Data quality** signals, baseline = the `transformed_data` asset,
   schedule = daily (or "run now" to test immediately).

---

## Track B — CLI / Scripts (Infrastructure-as-Code)

Everything below is scripted. Set these once per shell session:

```bash
export RESOURCE_GROUP=rg-taxi-mlops   # must match infra/main.parameters.json
export WORKSPACE_NAME=aml-taxi        # only needed if you skip step B1's auto-detect
```

### B1. Provision infrastructure
```bash
./scripts/01_deploy_infra.sh
```
Runs `az deployment sub create` with [infra/main.bicep](infra/main.bicep), provisioning
a Resource Group + Storage Account + Key Vault + Application Insights + Azure ML
Workspace + an autoscaling (`0`–`2` node) Compute Cluster named `taxi-cpu-cluster`.
Edit [infra/main.parameters.json](infra/main.parameters.json) to change region, name
prefix or VM size.

> ⚠️ This creates **real, billable** resources. The compute cluster scales to zero when
> idle, so you only pay for compute while a job is actually running — but the
> workspace/storage/Key Vault incur a small monthly cost regardless.

### B2. Register the environment
```bash
./scripts/02_set_defaults_and_env.sh
```
Sets the `az` CLI defaults (resource group + workspace) and registers
`taxi-fare-train-env` from [environment/train-env.yml](environment/train-env.yml) /
[environment/conda.yaml](environment/conda.yaml).

### B3. Submit the training pipeline
```bash
./scripts/03_run_pipeline.sh
```
Runs `az ml job create --file pipeline.yml --stream`, registering the 4 components
on the fly and streaming logs to your terminal (with a link to the Studio job graph).
Check **Jobs** → metrics, and **Models** for `taxi-model` if `deploy_flag == 1`.

### B4. Deploy the Managed Online Endpoint
```bash
./scripts/04_deploy_endpoint.sh
```
Runs `az ml online-endpoint create` + `az ml online-deployment create` from
[deployment/endpoint.yml](deployment/endpoint.yml) and
[deployment/deployment.yml](deployment/deployment.yml), pointing at the latest
`taxi-model` version and the same `taxi-fare-train-env` environment
(deployment takes ~10–15 minutes to provision).

### B5. Test the endpoint
```bash
./scripts/05_test_endpoint.sh
```
Invokes the endpoint with [deployment/sample-request.json](deployment/sample-request.json)
via `az ml online-endpoint invoke`. You can also call it over plain HTTPS:

```bash
SCORING_URL=$(az ml online-endpoint show --name taxi-fare-endpoint --query scoring_uri -o tsv)
KEY=$(az ml online-endpoint get-credentials --name taxi-fare-endpoint --query primaryKey -o tsv)

curl -X POST "$SCORING_URL" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d @deployment/sample-request.json
```

### B6. Monitoring
Model Monitoring (data drift/quality schedules) is currently set up via Portal UI only
in this lab (see [A7](#a7-enable-monitoring)) — the CLI v2 `az ml schedule create`
monitoring schema is newer/less stable at the time of writing. Feel free to contribute
a CLI equivalent.

---

## 4. Model details

- **Features** (20 columns, identical across `train.py` / `evaluate.py` /
  `deployment/score.py`): trip `distance`, pickup/dropoff lat-long, `passengers`,
  `store_forward`, `vendor`, and weekday/month/day/hour/minute/second decomposed from
  both pickup and dropoff timestamps.
- **Target**: `cost` (fare amount).
- **Model**: `sklearn.linear_model.LinearRegression`, logged with `mlflow.sklearn.autolog()`.
- **Promotion gate**: `evaluate-job` only sets `deploy_flag = 1` (triggering
  `register-job`) when no model is registered yet, or the new model's test-set R² is
  ≥ the best currently-registered model's R² — a simple champion/challenger gate.

## 5. What was changed vs. the original reference repo

- `prep.py`: reads files by **name** (`green`/`yellow` substring match), not by
  `os.listdir` order (unstable across OS/runs); only reads `.csv` files (ignores the
  `*_data.yml` sidecar files in `data/`); uses `pd.concat` instead of the removed
  `DataFrame.append` (pandas 2.0+).
- `evaluate.py`: `Model.download()` returns a **directory**, not a file — the original
  code tried to `pickle.load` the directory directly. Fixed to open `model.sav` inside it.
- `environment/`: custom conda environment instead of the deprecated curated
  environment `AzureML-sklearn-0.24-ubuntu18.04-py37-cpu`.
- `infra/`: added Bicep templates to provision everything as code instead of manual
  Portal clicks — a core MLOps Engineer skill (also used by Track B).
- `deployment/`: added a Managed Online Endpoint (score.py + CLI v2 specs), which the
  original reference repo only sketches.

## 6. Lessons learned / troubleshooting

Two non-obvious environment bugs were hit (and fixed) while building this lab —
documented here since they're easy to hit again:

1. **`ModuleNotFoundError: No module named 'pkg_resources'`** when importing
   `azureml.core`, even though `setuptools` was listed in the conda environment.
   Root cause: Azure ML's custom-environment build installs `pip:`-listed packages
   into their **own isolated venv**, layered on top of the conda-level packages — so a
   package declared at the **conda level** (next to `pip`, not inside the `pip:` block)
   is invisible to anything installed via `pip:` (like `azureml-core`). **Fix:** declare
   `setuptools` *inside* the `pip:` list, in the same place as `azureml-core`.
2. **Managed Online Endpoint deployment fails at container start** with
   `"A required package azureml-inference-server-http is missing"`. The training
   environment doesn't need this package, but the inference container does — add
   `azureml-inference-server-http` to the same conda environment before deploying.

## 7. Roadmap

- [ ] **CI/CD**: GitHub Actions workflow to re-run the pipeline on every push
  (`.github/workflows/`), authenticating via OIDC workload identity federation
  instead of a static secret.

## License

[MIT](LICENSE) — see the LICENSE file for details.

## Acknowledgements

Based on the architecture of
[Azure/mlops-project-classical-ml](https://github.com/Azure/mlops-project-classical-ml),
part of Microsoft's [Azure/mlops-v2](https://github.com/Azure/mlops-v2) accelerator.
