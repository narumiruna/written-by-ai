package main

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
	"time"
)

const boardSize = 4

func main() {
	rand.Seed(time.Now().UnixNano())
	board := newBoard()
	// 初始隨機產生兩個數字
	addRandomTile(board)
	addRandomTile(board)

	scanner := bufio.NewScanner(os.Stdin)
	for {
		printBoard(board)
		fmt.Print("請輸入方向 (w:上, a:左, s:下, d:右): ")
		scanner.Scan()
		input := scanner.Text()

		// 檢查輸入是否有效
		if input != "w" && input != "a" && input != "s" && input != "d" {
			fmt.Println("輸入錯誤，請重新輸入!")
			continue
		}

		var moved bool
		switch input {
		case "w":
			moved = moveUp(board)
		case "a":
			moved = moveLeft(board)
		case "s":
			moved = moveDown(board)
		case "d":
			moved = moveRight(board)
		}

		// 如果移動無效則重新讀取
		if !moved {
			fmt.Println("無法移動，請試試其他方向")
			continue
		}

		// 移動後新增一個隨機數字
		addRandomTile(board)

		// 檢查是否遊戲結束
		if isGameOver(board) {
			printBoard(board)
			fmt.Println("遊戲結束!")
			break
		}
	}
}

// 建立一個空的 board
func newBoard() [][]int {
	board := make([][]int, boardSize)
	for i := range board {
		board[i] = make([]int, boardSize)
	}
	return board
}

// 印出目前的 board 狀態
func printBoard(board [][]int) {
	fmt.Println("---------------------")
	for _, row := range board {
		for _, val := range row {
			if val == 0 {
				fmt.Printf(".\t")
			} else {
				fmt.Printf("%d\t", val)
			}
		}
		fmt.Println()
	}
	fmt.Println("---------------------")
}

// 在 board 上的空格隨機加入一個新數字（90% 產生 2，10% 產生 4）
func addRandomTile(board [][]int) {
	empties := [][2]int{}
	for i := 0; i < boardSize; i++ {
		for j := 0; j < boardSize; j++ {
			if board[i][j] == 0 {
				empties = append(empties, [2]int{i, j})
			}
		}
	}
	if len(empties) == 0 {
		return
	}
	idx := rand.Intn(len(empties))
	i, j := empties[idx][0], empties[idx][1]
	if rand.Float32() < 0.9 {
		board[i][j] = 2
	} else {
		board[i][j] = 4
	}
}

// 將一列的數字向左壓縮（去除中間的 0）
func compress(row []int) ([]int, bool) {
	newRow := []int{}
	moved := false
	for _, val := range row {
		if val != 0 {
			newRow = append(newRow, val)
		}
	}
	// 補回 0 到尾端
	for len(newRow) < len(row) {
		newRow = append(newRow, 0)
	}
	// 檢查是否有變動
	for i := 0; i < len(row); i++ {
		if newRow[i] != row[i] {
			moved = true
			break
		}
	}
	return newRow, moved
}

// 合併相鄰且相同的數字（由左到右）
func merge(row []int) ([]int, bool) {
	moved := false
	for i := 0; i < len(row)-1; i++ {
		if row[i] != 0 && row[i] == row[i+1] {
			row[i] *= 2
			row[i+1] = 0
			moved = true
			i++ // 跳過下一格
		}
	}
	return row, moved
}

// 向左移動
func moveLeft(board [][]int) bool {
	moved := false
	for i := 0; i < boardSize; i++ {
		row, moved1 := compress(board[i])
		row, moved2 := merge(row)
		row, _ = compress(row)
		board[i] = row
		if moved1 || moved2 {
			moved = true
		}
	}
	return moved
}

// 反轉一列（用於右移動）
func reverse(row []int) []int {
	newRow := make([]int, len(row))
	for i, v := range row {
		newRow[len(row)-1-i] = v
	}
	return newRow
}

// 向右移動
func moveRight(board [][]int) bool {
	moved := false
	for i := 0; i < boardSize; i++ {
		reversed := reverse(board[i])
		row, moved1 := compress(reversed)
		row, moved2 := merge(row)
		row, _ = compress(row)
		newRow := reverse(row)
		board[i] = newRow
		if moved1 || moved2 {
			moved = true
		}
	}
	return moved
}

// 將 board 轉置（用於上下移動）
func transpose(board [][]int) [][]int {
	newB := newBoard()
	for i := 0; i < boardSize; i++ {
		for j := 0; j < boardSize; j++ {
			newB[j][i] = board[i][j]
		}
	}
	return newB
}

// 向上移動：轉置後使用向左移動，再轉置回來
func moveUp(board [][]int) bool {
	transposed := transpose(board)
	moved := moveLeft(transposed)
	newB := transpose(transposed)
	for i := 0; i < boardSize; i++ {
		board[i] = newB[i]
	}
	return moved
}

// 向下移動：轉置後使用向右移動，再轉置回來
func moveDown(board [][]int) bool {
	transposed := transpose(board)
	moved := moveRight(transposed)
	newB := transpose(transposed)
	for i := 0; i < boardSize; i++ {
		board[i] = newB[i]
	}
	return moved
}

// 判斷遊戲是否結束（無空格且無法合併）
func isGameOver(board [][]int) bool {
	for i := 0; i < boardSize; i++ {
		for j := 0; j < boardSize; j++ {
			if board[i][j] == 0 {
				return false
			}
		}
	}
	// 檢查水平方向是否可以合併
	for i := 0; i < boardSize; i++ {
		for j := 0; j < boardSize-1; j++ {
			if board[i][j] == board[i][j+1] {
				return false
			}
		}
	}
	// 檢查垂直方向是否可以合併
	for j := 0; j < boardSize; j++ {
		for i := 0; i < boardSize-1; i++ {
			if board[i][j] == board[i+1][j] {
				return false
			}
		}
	}
	return true
}
