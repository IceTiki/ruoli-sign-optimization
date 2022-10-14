#!/usr/bin/env bash
# new Env("今日校园签到")
# cron 30 8 * * * startCpdaily.sh

# 初始化青龙环境
dir_shell=$QL_DIR/shell
. "$dir_shell"/share.sh

cpdaily_repo="IceTiki_ruoli-sign-optimization"
config_file="$(pwd)/config.yml"

echo "repo目录：$dir_repo"
cpdaily_repo_dir="$(find "$dir_repo" -type d -iname "$cpdaily_repo" | head -1)"
# shellcheck disable=SC2028
echo "脚本目录：$cpdaily_repo_dir\n"

cd "$cpdaily_repo_dir" || exit
python3 index.py -c "$config_file" -e qinglong
