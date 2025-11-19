const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');
const hash = require('hash-sum');

module.exports = {
    entry: './index.ts',
    output: {
        filename: `bundle-${hash(Date.now().toString())}.js`,
        path: path.resolve(__dirname, 'dist')
    },
    mode: 'production',
    optimization: {
        minimize: true,
        minimizer: [new TerserPlugin({
            terserOptions: {
                format: {
                    comments: false,
                },
                mangle: true,
                compress: {
                    drop_console: true,
                },
            },
            extractComments: false,
            
        })],

    },
    module: {
        rules: [
            {
                test: /\.ts$/,
                use: 'ts-loader',
                exclude: /node_modules/
            }
        ]
    },
    resolve: {
        extensions: ['.ts', '.js']
    },
};