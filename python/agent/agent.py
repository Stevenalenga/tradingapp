import argparse
import os
import sys
import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Local imports relative to project layout
# Ensure python/ is on sys.path when running as a module
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config import Config
from utils.logger import setup_logger
from storage.csv_storage import CSVStorage
from storage.json_storage import JSONStorage


@dataclass
class AgentConfig:
    config_path: str
    api_key_path: str = "llm.openrouter.api_key"
    model_path: str = "llm.openrouter.model"
    default_model: str = "openrouter/auto"
    data_dir: str = os.path.join(PROJECT_ROOT, "data")
    viz_dir: str = os.path.join(PROJECT_ROOT, "visualization")

class TradingAgent:
    """
    Agent that can:
      - Update OpenRouter API key in config.yaml
      - Invoke python.main:main() workflow on demand
      - Discover latest artifacts (data and visualization)
      - Analyze artifacts and produce an LLM-backed narrative using OpenRouter
    """

    def __init__(self, agent_cfg: AgentConfig):
        self.agent_cfg = agent_cfg
        self.logger = setup_logger("agent", "INFO", os.path.join(PROJECT_ROOT, "logs", "agent.log"))
        self.config = Config(agent_cfg.config_path)
        if not isinstance(self.config.get_all(), dict) or not self.config.get_all():
            raise RuntimeError(f"Configuration missing or invalid at {agent_cfg.config_path}")

        # Ensure LLM model default exists if not set
        if self.config.get(agent_cfg.model_path) is None:
            self.config.set(agent_cfg.model_path, agent_cfg.default_model)
            self.config.save_config()

    # -----------------------
    # API Key Management
    # -----------------------
    def update_api_key(self, api_key: str) -> None:
        """
        Update the OpenRouter API key within config.yaml under llm.openrouter.api_key
        """
        self.logger.info("Updating OpenRouter API key in configuration")
        self.config.set(self.agent_cfg.api_key_path, api_key)
        ok = self.config.save_config()
        if not ok:
            raise RuntimeError("Failed to save updated API key to configuration")
        self.logger.info("API key updated successfully")

    def read_api_key(self) -> Optional[str]:
        return self.config.get(self.agent_cfg.api_key_path)

    # -----------------------
    # Orchestration
    # -----------------------
    def run_main(self, sources: Optional[List[str]] = None, schedule: str = "once", verbose: bool = False) -> int:
        """
        Invoke the main application pipeline programmatically.
        To prevent GUI-backend issues with Matplotlib on non-main threads or headless environments,
        we set MPLBACKEND=Agg for the subprocess call.
        Gracefully handle Ctrl+C to terminate the child process.
        """
        import subprocess
        env = os.environ.copy()
        # Force non-interactive backend to avoid Tkinter/Tcl main loop errors
        env.setdefault("MPLBACKEND", "Agg")

        cmd = [
            sys.executable,
            os.path.join(PROJECT_ROOT, "main.py")
        ]
        if self.agent_cfg.config_path:
            cmd += ["--config", self.agent_cfg.config_path]
        if sources:
            cmd += ["--sources", ",".join(sources)]
        if schedule:
            cmd += ["--schedule", schedule]
        if verbose:
            cmd += ["--verbose"]

        self.logger.info(f"Running main pipeline: {' '.join(cmd)}")
        try:
            # Use Popen to allow sending signals, and wait to capture KeyboardInterrupt
            proc = subprocess.Popen(cmd, cwd=PROJECT_ROOT, env=env)
            try:
                return_code = proc.wait()
            except KeyboardInterrupt:
                self.logger.info("KeyboardInterrupt received, terminating scraping process...")
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except Exception:
                        proc.kill()
                finally:
                    return_code = -2
            self.logger.info(f"Main pipeline exited with code {return_code}")
            return return_code
        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt received before process start.")
            return -2

    # -----------------------
    # Artifact Discovery
    # -----------------------
    def _list_files_sorted(self, directory: str, extensions: Tuple[str, ...]) -> List[str]:
        files: List[Tuple[float, str]] = []
        if not os.path.isdir(directory):
            return []
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isfile(path) and name.lower().endswith(extensions):
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    mtime = 0.0
                files.append((mtime, path))
        files.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in files]

    def discover_latest_data_file(self) -> Optional[str]:
        # Prefer CSV/JSON generated by storage
        candidates = self._list_files_sorted(self.agent_cfg.data_dir, (".csv", ".json"))
        return candidates[0] if candidates else None

    def discover_latest_visualization(self) -> Optional[str]:
        # Prefer images produced by DataVisualizer (png/jpg/svg/pdf)
        candidates = self._list_files_sorted(self.agent_cfg.viz_dir, (".png", ".jpg", ".jpeg", ".svg", ".pdf", ".html"))
        return candidates[0] if candidates else None

    # -----------------------
    # Analysis
    # -----------------------
    def _read_tabular_preview(self, path: str, max_rows: int = 20) -> Dict:
        """
        Load a quick preview of the dataset with schema and descriptive stats.
        Does not load entire large files into memory unnecessarily.
        """
        import pandas as pd

        info: Dict = {"path": path}
        try:
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path)
            elif path.lower().endswith(".json"):
                # Attempt to normalize various JSON shapes into a DataFrame
                with open(path, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                if isinstance(obj, list):
                    df = pd.DataFrame(obj)
                elif isinstance(obj, dict):
                    # dictionary of homogeneous objects
                    if all(isinstance(v, dict) for v in obj.values()):
                        rows = [{"id": k, **v} for k, v in obj.items()]
                        df = pd.DataFrame(rows)
                    else:
                        df = pd.DataFrame([obj])
                else:
                    df = pd.DataFrame({"value": [obj]})
            else:
                return {"path": path, "error": "unsupported data extension"}

            info["shape"] = list(df.shape)
            info["columns"] = df.columns.tolist()
            # basic type inference
            dtypes = {c: str(t) for c, t in df.dtypes.items()}
            info["dtypes"] = dtypes
            # sample rows
            info["head"] = df.head(min(max_rows, len(df))).to_dict(orient="records")

            # numeric summary
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                desc = df[numeric_cols].describe().to_dict()
                info["describe_numeric"] = desc
            else:
                info["describe_numeric"] = {}

            return info
        except Exception as e:
            return {"path": path, "error": f"failed to read dataset: {e}"}

    def _visual_summary(self, path: str) -> Dict:
        """
        Provide a lightweight summary for the visualization artifact.
        For images, we capture filename and extension; for HTML, we attempt to extract title if present.
        """
        info: Dict = {"path": path}
        if not path:
            return {"error": "no visualization path"}
        name = os.path.basename(path)
        info["filename"] = name
        ext = os.path.splitext(name)[1].lower()
        info["extension"] = ext

        if ext == ".html":
            try:
                # extract <title> if available
                title = None
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read(4096)
                import re
                m = re.search(r"<title>(.*?)</title>", txt, re.IGNORECASE | re.DOTALL)
                if not m:
                    m = re.search(r"<h1[^>]*>(.*?)</h1>", txt, re.IGNORECASE | re.DOTALL)
                if m:
                    title = re.sub(r"\s+", " ", m.group(1)).strip()
                info["title"] = title
            except Exception as e:
                info["title_error"] = str(e)

        return info

    def _select_artifacts_for_analysis(self, analyze_sources: Optional[List[str]], analyze_all: bool,
                                       explicit_data: Optional[str], explicit_viz: Optional[str]) -> List[Dict[str, Optional[str]]]:
        """
        Build a list of artifact pairs (data_path, viz_path, source_hint) to analyze based on flags and available files.
        - If explicit paths provided, return a single pair.
        - If analyze_sources provided, match files by source name presence in filename.
        - If analyze_all, include all discovered data files with best matching viz by timestamp.
        - Otherwise, return the latest single pair.
        """
        # If explicit single selection
        if explicit_data or explicit_viz:
            return [{"data": explicit_data or self.discover_latest_data_file(),
                     "viz": explicit_viz or self.discover_latest_visualization(),
                     "source": None}]

        data_files = self._list_files_sorted(self.agent_cfg.data_dir, (".csv", ".json"))
        viz_files = self._list_files_sorted(self.agent_cfg.viz_dir, (".png", ".jpg", ".jpeg", ".svg", ".pdf", ".html"))

        def pick_best_viz_for(data_path: Optional[str]) -> Optional[str]:
            if not data_path or not viz_files:
                return None
            # naive pairing by closest mtime
            try:
                d_mtime = os.path.getmtime(data_path)
            except OSError:
                return None
            best = None
            best_dt = float("inf")
            for vp in viz_files:
                try:
                    v_m = os.path.getmtime(vp)
                except OSError:
                    continue
                dt = abs(v_m - d_mtime)
                if dt < best_dt:
                    best_dt = dt
                    best = vp
            return best

        # If analyze_sources provided, filter data_files by substring match
        if analyze_sources:
            selected = []
            lowered = [s.lower() for s in analyze_sources]
            for df in data_files:
                name = os.path.basename(df).lower()
                # match any requested source token in filename
                if any(tok in name for tok in lowered):
                    selected.append({"data": df, "viz": pick_best_viz_for(df), "source": None})
            if selected:
                return selected
            # Fallback: nothing matched, return latest single
            latest = self.discover_latest_data_file()
            return [{"data": latest, "viz": pick_best_viz_for(latest), "source": None}]

        # If analyze_all, return all data files
        if analyze_all:
            return [{"data": df, "viz": pick_best_viz_for(df), "source": None} for df in data_files]

        # Default: latest pair
        latest = self.discover_latest_data_file()
        return [{"data": latest, "viz": pick_best_viz_for(latest), "source": None}]

    def analyze(self, data_path: Optional[str] = None, viz_path: Optional[str] = None, model: Optional[str] = None,
                analyze_sources: Optional[List[str]] = None, analyze_all: bool = False) -> Dict:
        """
        Use OpenRouter to generate an analysis of selected data and visualizations.
        Supports multi-artifact analysis via --analyze-sources or --analyze-all.
        """
        api_key = self.read_api_key()
        if not api_key:
            raise RuntimeError("OpenRouter API key not set in config.yaml under llm.openrouter.api_key")

        # Build artifact selection list
        selections = self._select_artifacts_for_analysis(analyze_sources, analyze_all, data_path, viz_path)

        reports: List[Dict] = []
        notes_global: List[str] = []

        for sel in selections:
            dpath = sel.get("data")
            vpath = sel.get("viz")

            payload: Dict = {
                "timestamp": datetime.utcnow().isoformat(),
                "data_preview": None,
                "visual_summary": None,
                "notes": [],
            }

            if dpath:
                payload["data_preview"] = self._read_tabular_preview(dpath)
            else:
                payload["notes"].append("No data file found in ./python/data")

            if vpath:
                payload["visual_summary"] = self._visual_summary(vpath)
            else:
                payload["notes"].append("No visualization found in ./python/visualization")

            # Construct prompt for LLM
            instruction = (
                "You are a data analyst. Given a dataset preview and a visualization summary, "
                "produce a concise, actionable analysis of the scraped data. "
                "Include: 1) Notable trends, 2) Outliers or anomalies, 3) Suggested follow-up visualizations, "
                "4) Trading-relevant insights. Keep it under 250 words."
            )
            user_content = json.dumps(payload, indent=2)

            model_name = model or self.config.get(self.agent_cfg.model_path) or self.agent_cfg.default_model

            try:
                analysis_text = self._call_openrouter(
                    api_key=api_key,
                    model=model_name,
                    system_prompt=instruction,
                    user_payload=user_content,
                )
            except KeyboardInterrupt:
                self.logger.info("KeyboardInterrupt received, aborting analysis request.")
                raise

            reports.append({
                "model": model_name,
                "analysis": analysis_text,
                "artifacts": {
                    "data": dpath,
                    "visualization": vpath,
                },
                "context": payload,
            })

        # Persist combined analysis as JSON in data dir
        out_name = f"agent_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out_path = os.path.join(self.agent_cfg.data_dir, out_name)
        os.makedirs(self.agent_cfg.data_dir, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"reports": reports}, f, indent=2)
        self.logger.info(f"Wrote analysis bundle to {out_path}")

        # For console output, if single report return its shape, otherwise summarize
        if len(reports) == 1:
            return reports[0]
        else:
            return {
                "count": len(reports),
                "reports": [{"artifacts": r["artifacts"], "analysis": r["analysis"], "model": r["model"]} for r in reports],
                "output_file": out_path,
            }

    # -----------------------
    # OpenRouter client
    # -----------------------
    def _call_openrouter(self, api_key: str, model: str, system_prompt: str, user_payload: str) -> str:
        """
        Minimal OpenRouter client using requests. Avoids adding heavy SDK dependencies.
        Adds robust error handling for invalid API keys and rate limits.
        """
        import requests

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
            "temperature": 0.2,
            "max_tokens": 600,
        }

        try:
            resp = requests.post(url, headers=headers, json=body, timeout=60)
        except KeyboardInterrupt:
            # Allow Ctrl+C to bubble after logging
            raise
        except requests.RequestException as e:
            raise RuntimeError(f"OpenRouter network/request error: {e}")

        # Handle non-200s with specific messages
        if resp.status_code == 401:
            # Unauthorized - likely invalid or missing API key
            # Try to extract message from JSON if available
            try:
                err = resp.json()
            except Exception:
                err = resp.text
            raise RuntimeError(f"OpenRouter authentication failed (401). Check your API key in config.yaml or OPENROUTER_API_KEY. Details: {err}")
        if resp.status_code == 403:
            # Forbidden - may indicate invalid key scope or account issue
            try:
                err = resp.json()
            except Exception:
                err = resp.text
            raise RuntimeError(f"OpenRouter access forbidden (403). Your key may lack permissions or be restricted. Details: {err}")
        if resp.status_code == 429:
            # Rate limit
            retry_after = resp.headers.get("Retry-After", "unknown")
            raise RuntimeError(f"OpenRouter rate limited (429). Retry after {retry_after} seconds.")
        if resp.status_code >= 400:
            # Other client/server errors
            try:
                err = resp.json()
            except Exception:
                err = resp.text
            raise RuntimeError(f"OpenRouter request failed: {resp.status_code} {err}")

        # Parse response
        try:
            data = resp.json()
            # Defensive checks
            choices = data.get("choices")
            if not choices:
                raise RuntimeError(f"OpenRouter response missing 'choices': {data}")
            msg = choices[0].get("message", {})
            content = msg.get("content")
            if not content:
                raise RuntimeError(f"OpenRouter response missing message content: {data}")
            return content
        except Exception as e:
            raise RuntimeError(f"Failed to parse OpenRouter response: {e}; raw={resp.text}")

# -----------------------
# CLI
# -----------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Trading Agent CLI")
    parser.add_argument("--config", type=str, default=os.path.join(PROJECT_ROOT, "config.yaml"), help="Path to config.yaml")
    parser.add_argument("--update-key", type=str, help="Set and persist OpenRouter API key in config.yaml")
    parser.add_argument("--run-main", action="store_true", help="Run the main pipeline once (scrape + process + visualize)")
    parser.add_argument("--sources", type=str, help="Comma-separated list of sources to scrape")
    parser.add_argument("--analyze", action="store_true", help="Analyze latest artifacts only. If --run-main is also passed, analysis runs after main. Without --run-main, this behaves like --analyze-only.")
    parser.add_argument("--analyze-only", action="store_true", help="Run analysis only without scraping/scheduling (use latest existing dataset and visualization)")
    # Analysis selection flags
    parser.add_argument("--analyze-sources", type=str, help="Comma-separated list of sources to analyze (e.g., yahoo_finance,coingecko,alternative_me). If omitted and --analyze-all not set, falls back to latest single artifact discovery.")
    parser.add_argument("--analyze-all", action="store_true", help="Analyze all available artifacts found in ./python/data and ./python/visualization")
    parser.add_argument("--data-path", type=str, help="Optional explicit path to data file for analysis (csv/json)")
    parser.add_argument("--viz-path", type=str, help="Optional explicit path to visualization file for analysis (png/jpg/svg/pdf/html)")
    parser.add_argument("--model", type=str, help="Override LLM model for this analysis call")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose pipeline logs for main run")
    return parser.parse_args()

def main():
    args = parse_args()
    agent_cfg = AgentConfig(config_path=args.config)
    agent = TradingAgent(agent_cfg)

    # Update API key if provided
    if args.update_key:
        agent.update_api_key(args.update_key)

    # If --analyze is provided without --run-main, treat it as analyze-only.
    if args.analyze and not args.run_main:
        try:
            analyze_sources = [s.strip() for s in args.analyze_sources.split(",")] if hasattr(args, "analyze_sources") and args.analyze_sources else None
            result = agent.analyze(
                data_path=args.data_path,
                viz_path=args.viz_path,
                model=args.model,
                analyze_sources=analyze_sources,
                analyze_all=getattr(args, "analyze_all", False)
            )
            if isinstance(result, dict) and "analysis" in result:
                print("Model:", result["model"])
                print("Artifacts:", result["artifacts"])
                print("Analysis:\n", result["analysis"])
            else:
                print(f"Generated {result.get('count', 0)} analyses. Output file: {result.get('output_file')}")
                for i, rep in enumerate(result.get("reports", []), 1):
                    print(f"[{i}] Artifacts: {rep['artifacts']}")
                    print(rep["analysis"])
                    print("-" * 80)
        except KeyboardInterrupt:
            print("Analysis cancelled by user (Ctrl+C).")
        return

    # Analysis-only shortcut (skip scraping entirely) always takes precedence over run-main.
    if args.analyze_only:
        try:
            analyze_sources = [s.strip() for s in args.analyze_sources.split(",")] if hasattr(args, "analyze_sources") and args.analyze_sources else None
            result = agent.analyze(
                data_path=args.data_path,
                viz_path=args.viz_path,
                model=args.model,
                analyze_sources=analyze_sources,
                analyze_all=getattr(args, "analyze_all", False)
            )
            if isinstance(result, dict) and "analysis" in result:
                print("Model:", result["model"])
                print("Artifacts:", result["artifacts"])
                print("Analysis:\n", result["analysis"])
            else:
                print(f"Generated {result.get('count', 0)} analyses. Output file: {result.get('output_file')}")
                for i, rep in enumerate(result.get("reports", []), 1):
                    print(f"[{i}] Artifacts: {rep['artifacts']}")
                    print(rep["analysis"])
                    print("-" * 80)
        except KeyboardInterrupt:
            print("Analysis cancelled by user (Ctrl+C).")
        return

    # Optionally run main once
    if args.run_main:
        try:
            sources = [s.strip() for s in args.sources.split(",")] if args.sources else None
            rc = agent.run_main(sources=sources, schedule="once", verbose=args.verbose)
            if rc != 0 and rc != -2:
                sys.exit(rc)
            if rc == -2:
                print("Scraping cancelled by user (Ctrl+C).")
        except KeyboardInterrupt:
            print("Scraping cancelled by user (Ctrl+C).")
            return

    # Optionally analyze after run_main only
    if args.analyze and args.run_main:
        try:
            analyze_sources = [s.strip() for s in args.analyze_sources.split(",")] if hasattr(args, "analyze_sources") and args.analyze_sources else None
            result = agent.analyze(
                data_path=args.data_path,
                viz_path=args.viz_path,
                model=args.model,
                analyze_sources=analyze_sources,
                analyze_all=getattr(args, "analyze_all", False)
            )
            if isinstance(result, dict) and "analysis" in result:
                print("Model:", result["model"])
                print("Artifacts:", result["artifacts"])
                print("Analysis:\n", result["analysis"])
            else:
                print(f"Generated {result.get('count', 0)} analyses. Output file: {result.get('output_file')}")
                for i, rep in enumerate(result.get("reports", []), 1):
                    print(f"[{i}] Artifacts: {rep['artifacts']}")
                    print(rep["analysis"])
                    print("-" * 80)
        except KeyboardInterrupt:
            print("Analysis cancelled by user (Ctrl+C).")

if __name__ == "__main__":
    main()