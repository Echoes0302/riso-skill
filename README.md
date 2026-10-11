# riso · 孔版印刷

一种颜色一张版，一版一版「印」出来。满版底色、三色以内、套色微微对不准、网点颗粒、墨不匀、滚轮蹭出来的轮印。全部是 Python 一笔一笔画的，不是滤镜，不是生图模型。

![毛球球在哪里？](riso/example_cards.png)

## 起手

```
pip install pillow numpy scipy
python3 riso/example.py           # → riso/example.png，和包里那张一模一样
python3 riso/example_poster.py    # → 海报「毛球球与乌鸦」+ 分色预览
python3 riso/example_cards.py     # → cards/ 里五张小卡 + example_cards.png 合集
```

跑出来的图和包里的例图逐像素一致（seed 固定），一致就说明环境对了。

**Claude Code 用户**：把整个 `riso/` 目录放进 `~/.claude/skills/`，然后说「画成 Riso」「做一张孔版印刷风的小卡」就能叫出来。`SKILL.md` 是完整的方法：分版思维、参数手感、油墨组合、角色画法、踩过的坑。

## 画之前知道的一件事

Riso 好不好看，九成在设计：用哪几块颜色、怎么摆、有没有一个点子。颗粒和错位只是最后那层皮，而且要克制——错位小到让人觉得「好像没对准」就够了，浅色要用整齐的细网点，不然会像灰尘。`SKILL.md` 开头把这条讲透了。
