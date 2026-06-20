from src.retriever.retriever import retrieve

query = input("Search: ")
results = retrieve(query)

for r in results:
    print("=" * 60)
    print(f"File : {r['file']}")
    print(f"Name : {r['name']}")
    print(f"Type : {r['type']}")
    print(f"Lines: {r['start_line']} - {r['end_line']}")
    print(f"Distance: {r['distance']:.4f}")
    print()
    print(r["code"])
    print()
