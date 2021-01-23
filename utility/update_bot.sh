#!/bin/bash
cd /home/rpg_user/distr
rm -rf /home/rpg_user/distr/idle_rpg_bot
git clone https://github.com/qvant/idle_rpg_bot.git
rm -rf /home/rpg_user/distr/idle_rpg_bot/.gitignore
rm -rf /home/rpg_user/distr/idle_rpg_bot/.git
rm -rf /home/rpg_user/distr/idle_rpg_bot/.github
cp -a idle_rpg_bot/. /usr/app/idle_rpg_bot/