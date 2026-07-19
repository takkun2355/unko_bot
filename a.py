# 25日に習った数学
print(
    "2026/6/25 習った数学の範囲",
    "- 近似値と有効数字について学ぼう！ -",
    "近似値と有効数字について入力",
    "1: 近似値   - n >= α > n",
    "2: 有効数字 - n x 10 ^ n",
    "3: その他   - secret///",
    sep="\n"
)

N = int(input("数字を入力 >"))

if N == 3:
    print(
        "数学の範囲でその他なんて習ってるわけねーだろ",
        "頭湧いてんのか^^",
        sep="\n"
    )

elif N == 2:
    M, L = map(float, input("有効数字を計算する数と信頼できる数を入力。\n例: 127000 1270\n入力 >").split())

    if M == L:
        print("習っていないが予想で返答", M, sep="\n")
    else:
        L = int(L)
        LL = len(L) // 1
        LL = int(LL)
        for i in range(LL):
            print(10 ** (L * (len() - 1)), "10 ^", len() - 1)

elif N == 1:
    M, L = map(float, input("近似値を計算する数と未満数を入力。\n例: 102 1\n101.5 ≥ 102.0(a) > 102.5\n入力 >").split())
    
    print(M - (L / 2 or 0), ">=", M, ">", M + (L / 2 or 0))

elif N == 810:
    print("浅野中学校 Atcoder 一行得点3桁の恐怖", "yaju = 810", sep="\n")

elif N == 931:
    print("aga is bad smell!!")

else:
    print("簡単なことを聞いてるのにできないなんて。あっ驚いてないよ？", "参考: unko_bot cogs.roast.py", sep="\n")
