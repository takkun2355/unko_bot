#include <string>
#include <cstring>
#include <vector>
#include <map>
#include <random>

// ダミーのn-gramテーブル（実際はファイルから読み込む）
std::map<std::string, std::vector<std::string>> ngram_table = {
    {"こんにちは", {"、元気ですか？", "、今日はいい天気ですね。"}},
    {"元気ですか", {"？", "、私は元気です。"}},
    // ... 実際にはwikipedia等から構築
};

extern "C" {
    const char* generate_response(const char* user_input) {
        // ユーザー入力（日本語）をそのままキーとして使用（簡易版）
        std::string key(user_input);

        // n-gramテーブルから候補を取得
        auto it = ngram_table.find(key);
        if (it == ngram_table.end()) {
            return "（n-gramに登録されていない入力です）";
        }

        // ランダムに1つ選択
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, it->second.size() - 1);
        int idx = dis(gen);

        static std::string response;
        response = key + it->second[idx];  // 例: "こんにちは、元気ですか？"

        return response.c_str();
    }
}