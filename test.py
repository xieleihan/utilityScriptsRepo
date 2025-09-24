#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def main():
    data = {
        "192.168.150.10": "49a982150e9657bf047c5d15c28fb26a",
        "192.168.150.12": "a9f7e1ec3deb2664a7e9fdd56b899409",
        "192.168.150.13": "337bcf8f5a2e560d950bca818c8e9086",
        "192.168.150.14": "a3def22b15b7cd439cb945861a8f8540",
        "192.168.150.15": "a0fb8e03c99b17d7c63997ca96076216",
        "192.168.150.16": "404dbf3a16e8d8de87d09407031cc35d",
        "192.168.150.17": "a5925fa0647721693a1ef576fee24476",
        "192.168.150.18": "a50181ce6b0c7314ec9b01f424333a79",
        "192.168.150.19": "0fbb38221bfb4072b54bd5405329f0b0",
        "192.168.150.21": "dde98e977845d66f21437559e3ada2d9",
        "192.168.150.22": "a19741fc4ee1592bf7b0073b14f6ba2b",
        "192.168.150.23": "cbb6f1b99af2b723f972db37d93a2c9c",
        "192.168.150.24": "ac8d2d1c7a058edbdb585cbbd5f60dac",
        "192.168.150.25": "73f44d878b92f5216f0d795faf98b300",
        "192.168.150.26": "af3af01311e3a7e3d30d8040aef13b79",
        "192.168.150.28": "3646abe61e3e9a6f556f51f74dd6c877",
        "192.168.150.3": "a9a90568afb47685bf8cbca8002c249d",
        "192.168.150.30": "47b617e6292b8491e1946b7cdadb824d",
        "192.168.150.31": "58438833deba3636e52cbb3ff45e9ae8",
        "192.168.150.32": "f0a7843c4e15d18e63b0b9b8e37485f3",
        "192.168.150.33": "34448ce7964ac02d3ebf5984e1ef85fa",
        "192.168.150.34": "5680485f156809baf26fc659ab785efa",
        "192.168.150.35": "1a392ee98064d76622b88dab356779d8",
        "192.168.150.36": "484e296e7e89c12e4f16f41bad7303b2",
        "192.168.150.37": "56714dd86014a169c751031f41d88e5b",
        "192.168.150.4": "38249f17f3f37a7841fb754581bddf00",
        "192.168.150.40": "c445a5c86a95a3f5321ab42e6b91328c",
        "192.168.150.41": "0965b2049ac68ae0a6df34e2e0a510bd",
        "192.168.150.42": "0649e3ae84d2cf7657be940c1290ac32",
        "192.168.150.43": "83eaccb6ad697b75ac2afece6dc19678",
        "192.168.150.44": "683980209a853764a619552fad230079",
        "192.168.150.45": "46a743119f0aeda4d729dffb70647a98",
        "192.168.150.46": "4e9d0e6a9481649210cf45dfa557d43e",
        "192.168.150.47": "d79d13fb1fec58d052d3d52b54ffd534",
        "192.168.150.5": "33d35d8f6fab7b453a5d9b11eab64633",
        "192.168.150.6": "d265860f26e72e00fa7187e53269dc3b",
        "192.168.150.7": "116b10b176e0dc02f1d7f48c4406b2bb",
        "192.168.150.8": "9659f65440060385635dc8da60991eca",
        "192.168.150.9": "9a764b8e47743ede47ed40c17ae84326"
    }
    array = [
        "a9a90568afb47685bf8cbca8002c249d",
        "38249f17f3f37a7841fb754581bddf00",
        "33d35d8f6fab7b453a5d9b11eab64633",
        "d265860f26e72e00fa7187e53269dc3b",
        "116b10b176e0dc02f1d7f48c4406b2bb",
        "9659f65440060385635dc8da60991eca",
        "9a764b8e47743ede47ed40c17ae84326",
        "49a982150e9657bf047c5d15c28fb26a",
        "a9f7e1ec3deb2664a7e9fdd56b899409",
        "337bcf8f5a2e560d950bca818c8e9086",
        "a3def22b15b7cd439cb945861a8f8540",
        "a0fb8e03c99b17d7c63997ca96076216",
        "404dbf3a16e8d8de87d09407031cc35d",
        "a5925fa0647721693a1ef576fee24476",
        "a50181ce6b0c7314ec9b01f424333a79",
        "0fbb38221bfb4072b54bd5405329f0b0",
        "dde98e977845d66f21437559e3ada2d9",
        "a19741fc4ee1592bf7b0073b14f6ba2b",
        "cbb6f1b99af2b723f972db37d93a2c9c",
        "ac8d2d1c7a058edbdb585cbbd5f60dac",
        "73f44d878b92f5216f0d795faf98b300",
        "af3af01311e3a7e3d30d8040aef13b79",
        "d79d13fb1fec58d052d3d52b54ffd534",
        "3646abe61e3e9a6f556f51f74dd6c877",
        "47b617e6292b8491e1946b7cdadb824d",
        "58438833deba3636e52cbb3ff45e9ae8",
        "f0a7843c4e15d18e63b0b9b8e37485f3",
        "34448ce7964ac02d3ebf5984e1ef85fa",
        "5680485f156809baf26fc659ab785efa",
        "1a392ee98064d76622b88dab356779d8",
        "484e296e7e89c12e4f16f41bad7303b2",
        "56714dd86014a169c751031f41d88e5b",
        "4e9d0e6a9481649210cf45dfa557d43e",
        "c445a5c86a95a3f5321ab42e6b91328c",
        "0649e3ae84d2cf7657be940c1290ac32",
        "46a743119f0aeda4d729dffb70647a98",
        "683980209a853764a619552fad230079",
        "0965b2049ac68ae0a6df34e2e0a510bd",
        "83eaccb6ad697b75ac2afece6dc19678"
    ]

    set_data_values = set(data.values())
    set_array = set(array)

    print(f"data 中的值数量: {len(set_data_values)}")
    print(f"数组中的值数量: {len(set_array)}")

    if set_data_values == set_array:
        print("完全一致！所有值都匹配，无多余或缺失。")
    else:
        missing_in_array = set_data_values - set_array
        missing_in_data = set_array - set_data_values
        if missing_in_array:
            print("数组中缺失以下值：")
            for v in missing_in_array:
                print(f"   {v}")
        if missing_in_data:
            print("数组中包含 data 中不存在的值：")
            for v in missing_in_data:
                print(f"   {v}")

if __name__ == "__main__":
    main()