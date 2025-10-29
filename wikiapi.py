import wikipedia

# 设置 Wikipedia 语言为中文
wikipedia.set_lang("zh")

try:
    # 使用 page() 获取完整页面内容而不是 summary()
    page = wikipedia.page("")
    
    print(f"标题: {page.title}")
    print(f"URL: {page.url}")
    print(f"摘要: {page.summary[:200]}...")
    
    print(f"\n--- 所有章节 ---")
    if page.sections:
        for section in page.sections[:10]:  # 显示前10个章节
            print(f"  - {section}")
    
    print(f"\n--- 相关链接 (前10个) ---")
    if page.links:
        for link in list(page.links)[:10]:
            print(f"  - {link}")
    
    print(f"\n--- 参考资料 (前5个) ---")
    if page.references:
        for ref in page.references[:5]:
            print(f"  - {ref}")
    
    print(f"\n--- 图片链接 (前5个) ---")
    if page.images:
        for img in page.images[:5]:
            print(f"  - {img}")
    
    print(f"\n--- 完整内容 ---\n")
    print(page.content)
    
except wikipedia.exceptions.DisambiguationError as e:
    print(f"这是消歧义页面，可能的选项：")
    for option in e.options[:10]:  # 显示前10个选项
        print(f"  - {option}")
        
except wikipedia.exceptions.PageError:
    print("页面不存在，请检查关键词是否正确")
    
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")