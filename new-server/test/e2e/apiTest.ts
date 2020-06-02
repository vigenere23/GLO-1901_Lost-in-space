import * as io from 'socket.io-client'
import { NestServer } from '../../src/nest-server'
import { ConfigProvider } from '../../src/config/config.provider'

let server: NestServer
export let socket: SocketIOClient.Socket

export function setup(socketNamespace: string): void {
  beforeAll(async done => {
    server = await NestServer.create(ConfigProvider.get())
    server.start()
    done()
  })

  afterAll(() => {
    server.stop()
  })

  beforeEach(done => {
    socket = io.connect(server.address() + socketNamespace)
    socket.on('connect', () => {
      done()
    })
  })

  afterEach(() => {
    if (socket.connected) {
      socket.disconnect()
    }
  })
}
