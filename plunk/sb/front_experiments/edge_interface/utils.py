def discretize(arr, num_windows=200):
    step = len(arr) // num_windows
    dis = [np.mean(arr[i * step : i * (step + 1)]) for i in range(num_windows)]
    return np.array(dis)


def wav_complex_display(uploaded_file):
    bytes = bytes_from_uploaded(uploaded_file)
    st.audio(bytes)
    arr = arr_from_bytes(bytes)
    arr_d = discretize(arr)
    st.write(f"length = {len(arr)}")
    st.bar_chart(arr_d)


def arr_from_bytes(bytes, dtype="int16"):
    arr = sf.read(bytes, dtype=dtype)[0]

    return arr


def bytes_from_uploaded(uploaded_file):
    uploaded_file.seek(0)
    result = io.BytesIO(uploaded_file.read())

    return result
