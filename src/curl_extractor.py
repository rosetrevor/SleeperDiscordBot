def extract_curl_data(file_path: str = "assets/headers.txt") -> tuple[str, dict[str, str]]:
    endpoint = ""
    headers = {}
    data = {}
    with open(file_path) as f:
        for line in f:
            if line[0:4] == "curl":
                endpoint = line.split("'")[1]
            elif line[0:4] == "  --":
                continue
            elif line[0:4] == "  -X":
                continue  # This is for proxy, but do I need it?
            elif line[0:4] == "  -H":
                header_line = line.split("'")[1]
                header_key = header_line.split(":")[0]
                header_value = header_line.split(": ")[1]
                headers[header_key] = header_value
            elif line[0:4] == "  -d":
                raise NotImplementedError("cURL contains data, have not implemented parsing this")
            else:
                # raise ValueError(f"Unknown cURL line format ({line})")
                # TODO: Should fix that
                continue
    return endpoint, headers

                
if __name__ == "__main__":
    import requests
    url, headers = extract_curl_data("assets/player_headers.txt")
    response = requests.get(url, headers=headers)
    print(response.status_code)
