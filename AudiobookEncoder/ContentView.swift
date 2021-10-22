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
    @State private var qualityPresets: [String] = [" 96 Kbps, Stereo, 48 kHz", "128 Kbps, Stereo, 48 kHz", "256 Kbps, Stereo, 48 kHz", "320 Kbps, Stereo, 48 kHz"]
    @State private var selectedPreset: String = " 96 Kbps, Stereo, 48 kHz"
    @State private var active: Bool = true
    var audiofiles: [String] = ["Audiofile 1", "Audiofile 2", "Audiofile 3"]
    var body: some View {
        HStack {
            VStack {
                TextField("Title", text: $title)
                TextField("Author", text: $author)
                Menu("Presets") {
                    Button("Save Preset", action: { })
                    Divider()
                    Button("Perry Rhodan", action: { })
                }
                TextField("Comment", text: $comment)
                TextField("Genre", text: $genre)
                Text("Drag and Drop \nCover Artwork")
                    .frame(minWidth: 300, minHeight: 300)
                    .font(.title)
                    .overlay(RoundedRectangle(cornerRadius: 8)
                    .strokeBorder(style: StrokeStyle(lineWidth: 2.5, dash: [10])))
                    .foregroundColor(Color.gray)
                HStack {
                    TextField("Export Destination", text: $exportPath)
                    Button(action: { NSOpenPanel().runModal() }) {
                        Image(systemName: "folder.fill")
                    }
                }
                HStack {
                    Picker("Quality", selection: $selectedPreset){
                        ForEach(qualityPresets, id: \.self) { preset in
                            Button(preset, action: { })
                        }
                    }
                    .labelsHidden()
                    Button("Export", action: { print(selectedPreset) }).foregroundColor(active ? Color.green : Color.red)
                    Toggle("Active", isOn: $active).labelsHidden()
                }
            }
            .padding(.trailing, 10)
            .frame(maxWidth: 300)
            List {
                ForEach(audiofiles, id: \.self) { p in
                    Text(p)
                }
            }
            .frame(minWidth: 500)
        }
        .padding(10)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
