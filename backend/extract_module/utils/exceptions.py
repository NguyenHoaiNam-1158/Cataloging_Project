class APIError(Exception):
    #Lỗi được trả về khi không thể kết nối với API sau lượt retry
    pass

class ParsingError(Exception):
    #Lỗi được trả về khi kết quả bị ảo giác và không thể parse json
    pass