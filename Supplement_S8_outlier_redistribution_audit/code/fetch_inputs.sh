#!/bin/sh
# Download the public inputs of protocol S8 into raw/ and verify them against
# protocol/input_hashes_at_freeze.sha256. Third-party data are not redistributed.
set -eu
cd "$(dirname "$0")/.."
mkdir -p raw/dami raw/adbench raw/dami_eval
B=https://www.dbs.ifi.lmu.de/research/outlier-evaluation
curl -sfL -o raw/dami/literature.tar.gz "$B/input/literature.tar.gz"
curl -sfL -o raw/dami/semantic.tar.gz "$B/input/semantic.tar.gz"
C=3dac8221081e190f157d78e93bfa8867f90d0965
for f in 1_ALOI 14_glass 18_Ionosphere 21_Lymphography 28_pendigits 32_shuttle 41_Waveform 42_WBC 43_WDBC 46_WPBC \
         2_annthyroid 7_Cardiotocography 15_Hepatitis 17_InternetAds 27_PageBlocks 29_Pima 35_SpamBase 37_Stamps 44_Wilt; do
  curl -sfL -o "raw/adbench/$f.npz" "https://raw.githubusercontent.com/Minqi824/ADBench/$C/adbench/datasets/Classical/$f.npz"
done
curl -sfL -o raw/adbench/adbench_arxiv_2206.09426_html.html "https://arxiv.org/html/2206.09426v2"
echo "d44468af5335a952b618930c954851817661af241f499c82fd9ba7ef5d71c706  raw/adbench/adbench_arxiv_2206.09426_html.html" | shasum -a 256 -c -
grep -v 'PROTOCOL_S8.md' protocol/input_hashes_at_freeze.sha256 | shasum -a 256 -c -
mkdir -p raw/dami/x
tar xzf raw/dami/literature.tar.gz -C raw/dami/x
tar xzf raw/dami/semantic.tar.gz -C raw/dami/x
# Native ELKI evaluation files, one per DAMI variant of the 19 names
for f in raw/dami/x/*/*/*.arff; do
  g=$(echo "$f" | cut -d/ -f4); n=$(echo "$f" | cut -d/ -f5); v=$(basename "$f" .arff)
  case " ALOI Glass Ionosphere Lymphography PenDigits Shuttle Waveform WBC WDBC WPBC Annthyroid Cardiotocography Hepatitis InternetAds PageBlocks Pima SpamBase Stamps Wilt " in
    *" $n "*) ;; *) continue ;;
  esac
  o="raw/dami_eval/$v.evaluation.csv.gz"
  [ -s "$o" ] || curl -sfL -o "$o" "$B/DAMI/$g/$n/$v.evaluation.csv.gz"
done
curl -sfL -o raw/dami_eval_results_Glass.csv.gz "$B/DAMI/literature/Glass/Glass_withoutdupl_norm.results.csv.gz"
echo "inputs ready"
