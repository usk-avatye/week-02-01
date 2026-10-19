# 컴파일러를 만들어보자!!

# 기호-토큰 딕셔너리
symbol_kinds = {
    "+": "PLUS",
    "*": "STAR",
    "(": "LPAREN",
    ")": "RPAREN",
}

# 현재 위치에서 정수 '하나'를 읽는 함수
# 입력: (문자열, 숫자가 시작되는 인덱스)
# 출력: (이번 함수 호출로 읽은 정수, 다음 읽을 위치)
def read_integer(source: str, position: int):
    # 시작 인덱스가 가리키는 문자는 숫자다. 숫자가 아닌 문자를 만날 때까지 순회하면 된다.
    len_source = len(source)
    n = position
    nums = ''

    # 문자열 끝까지 순회
    # 중간에 숫자가 아닌 문자를 만나면 while문을 나옴
    # (이번 함수 호출로 읽은 정수, 다음 읽을 위치)를 return
    while len_source >= n + 1:
        if not source[n].isdigit() or not '0' <= source[n] <= '9':
            break
        else:
            nums = nums + source[n]
            n = n + 1
    return (int(nums), n)


# tokenizer 함수를 만들자!
# 입력: 원본 문자열
# 출력: 토큰을 입력 순서대로 받은 리스트
# 토큰 하나는 다음과 같은 튜플 형태(종류, 값, 위치)

def tokenizer(source):
    len_source = len(source)
    n = 0
    start = 0
    tokens = []

    while len_source >= n + 1:
        """
        1. 숫자를 만나면
            현재 위치를 토큰 시작 위치로 저장
            원본 문자열과 시작 위치를 read_integer 함수로 전송 후 반환된 정수 값으로 토큰 생성
            다음 위치는 그 함수가 반환한 위치로 갱신
        """
        if '0' <= source[n] <= '9':
            start = n
            integer_value, next_position = read_integer(source, start)
            token = ("INTEGER", integer_value, start)
            n = next_position
            tokens.append(token)

        # 2. 기호를 만나면 해당 토큰을 만들고 위치를 한 칸 이동
        elif source[n] in symbol_kinds:
            # (종류, 값, 위치)
            token = (symbol_kinds[source[n]], source[n], n)
            tokens.append(token)
            n = n + 1
        
        # 3. 공백(스페이스바, 탭, \n, \r)을 만나면 위치를 한 칸 이동
        elif source[n] in " \t\r\n":
            n = n + 1

        #4. 그 밖의 문자를 만나면 ValueError 발생. 오류 메시지에는 위치와 문자 표시!
        else:
            raise ValueError(f"위치 {n}: 허용하지 않은 문자 '{source[n]}'")
            
    # 5. 입력 끝에 도달하면 EOF 토큰을 추가하고 목록을 반환
    tokens.append(("EOF", None, len_source))
    return tokens