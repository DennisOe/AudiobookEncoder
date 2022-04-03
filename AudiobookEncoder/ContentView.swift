//
//  ContentView.swift
//  audiobookEncoder
//
//  Created by Dennis Oesterle on 13.03.21.
//

import SwiftUI




struct ContentView: View {
    @State private var title: String = ""
    @State private var author: String = ""
    @State private var comment: String = ""
    @State private var genre: String = ""
    @State private var exportPath: String = ""
    var qualityPresets: [String] = [" 96 Kbps, Stereo, 48 kHz", "128 Kbps, Stereo, 48 kHz", "256 Kbps, Stereo, 48 kHz", "320 Kbps, Stereo, 48 kHz"]
    @State private var selectedQualityPreset: String = " 96 Kbps, Stereo, 48 kHz"
    @State private var active: Bool = true
    @State private var audioBooks: [Audiobook] = [Audiobook(name: "Audiobook 1", files: ["AudiofileA 1.mp3", "AudiofileA 2.mp3", "AudiofileA 3.mp3"]),
                                   Audiobook(name: "Audiobook 2", files: ["AudiofileB 1.flac", "AudiofileB 2.flac", "AudiofileB 3.flac"]),
                                   Audiobook(name: "Audiobook 3", files: ["AudiofileC 1.m4a", "AudiofileC 2.m4a", "AudiofileC 3.m4a"]),]
    
    var audioBookPresets: [String] = ["Perry Rhodan", "Die drei Fragezeichen"]
    @State private var listSelection = Set<String>()
    
    var body: some View {
        HStack {
            VStack {
                TextField("Title", text: $title)
                TextField("Author", text: $author)
                Menu("Presets") {
                    Button("Save Preset", action: { })
                    Divider()
                    ForEach(audioBookPresets, id: \.self) { audioPreset in
                        Button(audioPreset, action: { })
                    }
                }
                TextField("Comment", text: $comment)
                TextField("Genre", text: $genre)
                Text("Drag and Drop \nCover Artwork")
                    .frame(minWidth: 300, minHeight: 300)
                    .font(.title)
                    .overlay(RoundedRectangle(cornerRadius: 8).strokeBorder(style: StrokeStyle(lineWidth: 2.5, dash: [10])))
                    .foregroundColor(Color.gray)
                HStack {
                    TextField("Export Destination", text: $exportPath)
                    Button(action: { NSOpenPanel().runModal() }) {
                        Image(systemName: "folder.fill")
                    }
                }
                HStack {
                    Picker("Quality", selection: $selectedQualityPreset) {
                        ForEach(qualityPresets, id: \.self) { qualityPreset in
                            Button(qualityPreset, action: { })
                        }
                    }
                    .labelsHidden()
                    Button("Export", action: { print(listSelection) }).foregroundColor(active ? Color.green : Color.red)
                    Toggle("Active", isOn: $active).labelsHidden()
                }
            }
            .padding(.trailing, 10)
            .frame(maxWidth: 300)
            List(selection: $listSelection) {
                Section(header: Text("Audiobooks (0/\(audioBooks.count))")) {
                    ForEach(audioBooks, id: \.name) { eachAudiobook in
                        DisclosureGroup(eachAudiobook.name) {
                            ForEach(eachAudiobook.files, id: \.self) { audiobookFile in
                                Text(audiobookFile)
                            }
                        }
                    }
                }
            }
            .frame(minWidth: 500)
        }
        .onChange(of: listSelection) { selection in change(trigger: selection.joined(separator: "-")) }
        .padding(10)
    }
    func change(trigger: String) {
        if !trigger.contains(".") {
            title = trigger
        }
    }
}

struct Audiobook: Hashable {
    let id = UUID()
    var name: String = ""
    var files: [String] = []
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
