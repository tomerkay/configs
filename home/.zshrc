# Must precede everything else in this file: until append_history is set, a
# shell killed during startup exits with /etc/zshrc's SAVEHIST=1000 and
# replaces ~/.zsh_history instead of appending to it.
HISTSIZE=1000000000
SAVEHIST=1000000000
HISTFILE="$HOME/.zsh_history"

setopt no_share_history
setopt inc_append_history
setopt extended_history
setopt append_history
setopt hist_ignore_all_dups
setopt hist_ignore_space

. ~/.zprofile
. ~/.zlogin

export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="my_theme"

plugins=(git fzf ssh-agent kubectl)

source $ZSH/oh-my-zsh.sh

source /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh

export LANG="en_US.UTF-8"
export LC_COLLATE="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
export LC_MESSAGES="en_US.UTF-8"
export LC_MONETARY="en_US.UTF-8"
export LC_NUMERIC="en_US.UTF-8"
export LC_TIME="en_US.UTF-8"

export LDFLAGS="-L/opt/homebrew/opt/libpq/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libpq/include"
export PKG_CONFIG_PATH="/opt/homebrew/opt/libpq/lib/pkgconfig"

autoload -Uz compinit && compinit

alias sudo='sudo '
alias watch='watch '
alias ll="ls -lah"
alias vscode="code"
alias gdelete="git push origin --delete"
unalias 1
unalias 2
unalias 3
unalias 4
unalias 5
unalias 6
unalias 7
unalias 8
unalias 9
setopt rmstarsilent

bindkey '\e[1;3C' forward-word   # Alt + Right Arrow
bindkey '\e[1;3D' backward-word  # Alt + Left Arrow

export DOCKER_DEFAULT_PLATFORM=linux/amd64

code() {
    VSCODE_CWD="$PWD" open -n -b "com.microsoft.VSCode" --args $*
}

delete_command() {
    if [ -z "$1" ]; then
        echo "Usage: delete_command <phrase>"
        return 1
    fi

    local phrase=$*
    local history_file="$HISTFILE"

    if [ -f "$history_file" ]; then
        # Entries are dropped whole: a multi-line command spans several lines,
        # continuations ending in "\", and removing just one of them leaves a
        # dangling "\" that swallows the entry after it.
        # LC_ALL=C: zsh metafies non-ASCII bytes, which are not valid UTF-8.
        # ENVIRON over awk -v: -v expands escape sequences in the phrase.
        local occur=$(LC_ALL=C phrase="$phrase" out="${history_file}.tmp" awk '
            BEGIN { p = ENVIRON["phrase"]; out = ENVIRON["out"]; printf "" > out }
            function flush() {
                if (rec == "") return
                if (index(rec, p)) n++; else printf "%s", rec > out
            }
            /^: [0-9]+:[0-9]+;/ && !cont { flush(); rec = "" }
            { rec = rec $0 "\n"; cont = /\\$/ }
            END { flush(); print n+0 }
        ' "$history_file") &&
            [ -s "${history_file}.tmp" ] &&
            mv "${history_file}.tmp" "$history_file"
        echo "Deleted commands ($occur occurrences) from $history_file containing: $phrase"
    fi
}

cdum() {
    cd ~/repos/atero-um
}

cdum-e() {
    cd ~/repos/atero-um-extended
}

cdvllm() {
    cd ~/repos/vllm
}

cdsglang() {
    cd ~/repos/sglang
}

cdgw() {
    cd ~/repos/atero-gw
}

venvum() {
    . ~/repos/atero-um/venv/bin/activate
}

venvum-e() {
    . ~/repos/atero-um-extended/venv-e/bin/activate
}

goum() {
    cdum
    venvum
    rehash
}

goum-e() {
    cdum-e
    venvum-e
    rehash
}

gcof() {
    if [ -n "$1" ]; then
        git checkout "$1"
    else
        git checkout $(git branch | fzf)
    fi
}

gdelb() {
    if [[ -n $1 ]]; then
        git branch -D "$1"
    else
        git branch | grep -v '\*' | sed 's/^..//' | fzf | xargs -r git branch -D
    fi
}

gdelb-r() {
    if [[ -n $1 ]]; then
        git push origin --delete "$1"
    else
        git branch | sed 's/^..//' | fzf | xargs -r git push origin --delete
    fi
}

grsh-r() {
  if [[ $# -ne 1 ]]; then
    BRANCH=`git rev-parse --abbrev-ref HEAD`
  else
    BRANCH=$1
  fi

  git fetch origin $BRANCH && git reset --hard origin/${BRANCH}
}

gpf-skip() {
    git commit -m "I'M HERE FOR SKIPPING CI [skip ci]" --allow-empty --no-verify
    git push --force-with-lease
    git reset HEAD~1
}

gcwip() {
    git commit -m "wip: Wip" --no-verify
}

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"  # This loads nvm
[ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"

export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh"

export NAMESPACE=***REMOVED***
export GITHUB_EMAIL=***REMOVED***
export GITHUB_USER=***REMOVED***
#export GITLAB_EMAIL=***REMOVED***
export GITLAB_EMAIL=***REMOVED***
export GITLAB_USER=***REMOVED***


function knodes() {
    local nodes pools body uptime
    nodes=$(k get nodes -o json) || return 1
    pools=$(print -r -- "$nodes" | jq -r '[.items[].metadata.labels["crusoe.ai/nodepool.id"]] | unique | join("|")')
    body=$(jq -nc --arg q "(time() - max by (vm_id) (crusoe_vm_boot_time{nodepool=~\"$pools\"})) / 86400" \
        '{jsonrpc:"2.0",id:1,method:"tools/call",params:{name:"live_promql_query",arguments:{query:$q,series_limit:500}}}')
    uptime=$(curl -sS -m 20 -X POST ***REMOVED*** \
        -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d "$body" \
        | jq -r '.result.content[0].text' \
        | sed -nE 's/.*vm_id="([^"]+)".*= ([0-9.]+).*/\1 \2/p')
    print -r -- "$nodes" | jq -r --arg up "$uptime" '
      def dage(t): ((now - (t | fromdateiso8601)) / 86400 | floor | tostring) + "d";
      ($up | split("\n") | map(select(length > 0) | split(" ")
             | {key: .[0], value: ((.[1] | tonumber | floor | tostring) + "d")}) | from_entries) as $uptime
      | ["NAME","STATUS","AGE","UPTIME","VERSION","INSTANCE-TYPE","USER"],
        (.items[] | [
          .metadata.name,
          (([.status.conditions[]? | select(.type == "Ready")
             | if .status == "True" then "Ready" else "NotReady" end]
            | if length == 0 then ["Unknown"] else . end)
           + (if .spec.unschedulable then ["SchedulingDisabled"] else [] end)
           | join(",")),
          dage(.metadata.creationTimestamp),
          ($uptime[.metadata.labels["crusoe.ai/instance.id"]] // "-"),
          .status.nodeInfo.kubeletVersion,
          (.metadata.labels["beta.kubernetes.io/instance-type"] // "<none>"),
          (.metadata.labels["atero/user"] // "<none>")
        ]) | @tsv' | column -t
}

function kshell() {
    kubectl "${@:2}" exec -it $1 -- /bin/bash
}

function kgdev() {
    k get pods | grep atero-dev | cut -d " " -f 1
}

function kgum() {
    k get pods | grep atero-um | cut -d " " -f 1
}

function kgkvcm() {
    k get pods | grep kvcm | cut -d " " -f 1
}

function kgvllm() {
    k get pods | grep model | cut -d " " -f 1
}

function kgsglang() {
    k get pods | grep sglang | cut -d " " -f 1
}

function watchp() {
  watch -n 1 kubectl get pods
}
source /Users/tkay/.zshrc.crusoe

[[ -s "/Users/tkay/.gvm/scripts/gvm" ]] && source "/Users/tkay/.gvm/scripts/gvm"
unset -f cd
export GPG_TTY=$(tty)
fpath=(~/.zsh/completion $fpath)
autoload -Uz compinit
compinit

