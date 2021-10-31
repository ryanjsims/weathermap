from rgbmatrix import RGBMatrix, RGBMatrixOptions

def setup_matrix() -> RGBMatrix:
    options = RGBMatrixOptions()
    options.cols = 64
    options.rows = 32
    options.chain_length = 2
    options.gpio_slowdown = 2
    return RGBMatrix(options=options)

matrix = setup_matrix()
matrix.Clear()