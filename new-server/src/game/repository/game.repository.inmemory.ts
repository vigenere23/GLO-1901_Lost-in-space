import { Game } from '../game'
import { GameId } from '../gameId'
import { GameRepository } from './game.repository'
import { Injectable } from '@nestjs/common'

@Injectable()
export class InMemoryGameRepository implements GameRepository {
    private games: Map<string, Game> = new Map()

    findAllAvailable(): Array<Game> {
        return Array
            .from(this.games.values())
            .filter(game => game.isAvailable)
    }

    findById(id: GameId) {
        return this.games.get(id.toString())
    }

    save(game: Game): void {
        if (this.games.has(game.id.toString())) {
            throw new Error(`game with id '${game.id}' already exists`)
        }

        this.games.set(game.id.toString(), game)
    }
}