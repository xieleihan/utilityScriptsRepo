import asyncio
import aiohttp
import json

API_URL = "http://127.0.0.1:9650/api/v1/comment-generation/generate"
INPUT_FILE = "./assets/sensitive_words_lines.txt"

async def send_request(session, text):
    payload = {
        "input": {
            "text": text,
            "language": "中文",
            "concern": "0"
        },
        "assistant_id": "comment_generation_assistant",
        "config": {"configurable": {}, "tags": []}
    }
    try:
        async with session.post(API_URL, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                is_safe = (
                    data.get("data", {})
                    .get("metadata", {})
                    .get("sensitive_check", {})
                    .get("is_safe")
                )
                return {"text": text.strip(), "is_safe": is_safe}
            else:
                return {"text": text.strip(), "is_safe": None, "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"text": text.strip(), "is_safe": None, "error": str(e)}

async def main():
    async with aiohttp.ClientSession() as session:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]

        true_count = 0
        false_count = 0
        false_texts = []

        # 串行处理：一个一个请求
        for i, line in enumerate(lines, 1):
            print(f"[{i}/{len(lines)}] Processing: {line.strip()[:50]}{'...' if len(line.strip()) > 50 else ''}")
            result = await send_request(session, line)

            # 立即打印当前结果
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print("-" * 60)

            # 统计
            is_safe = result.get("is_safe")
            if is_safe is True:
                true_count += 1
            elif is_safe is False:
                false_count += 1
                false_texts.append(result["text"])

        total = len(lines)

        # 最终汇总
        print("\n" + "="*60)
        print("✅ FINAL SUMMARY")
        print("="*60)
        print(f"Total: {total}")
        print(f"Safe (true): {true_count}")
        print(f"Not safe (false): {false_count}")

        if false_texts:
            print("\n--- Unsafe texts (is_safe = false) ---")
            for text in false_texts:
                print(text)
        else:
            print("\n✅ No unsafe texts found.")

if __name__ == "__main__":
    asyncio.run(main())